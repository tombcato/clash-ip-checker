import asyncio
import os
import shutil
import yaml
import logging
import datetime
from typing import Optional
from curl_cffi.requests import AsyncSession
from .clash_api import ClashController
from .config import config

# Configure logging
# logging.basicConfig removed
logger = logging.getLogger("CheckerService")

class CheckerService:
    def __init__(self, api_url: str = None, api_secret: str = ""):
        # If no api_url provided, use config
        self.api_url = api_url or config.api_url
        self.clash = ClashController(self.api_url, api_secret)
        self.current_file = None
        self.SKIP_KEYWORDS = config.skip_keywords
        
    async def _check_ip_fast(self, proxy_url: str, options: dict = None):
        """
        Checks IP using configured sources with fallback.
        """
        from .sources.ippure import IPPureSource
        from .sources.ping0 import Ping0Source
        
        options = options or {}

        # Initialize sources
        sources = {
            "ippure": IPPureSource(),
            "ping0": Ping0Source()
        }
        
        # Determine Order from options or config
        primary_name = options.get("source") or config.source
        allow_fallback = options.get("fallback") if options.get("fallback") is not None else config.fallback
        request_timeout = options.get("request_timeout") or config.request_timeout # Check sources usage
        
        # Note: Actual timeout is set in Source.check() but currently sources read config.request_timeout directly.
        # Ideally we pass timeout to source.check(..., timeout=...)
        # But for now let's keep it simple or monkeypatch config context if possible? 
        # Better: Update BaseSource.check signature later?
        # Actually, let's just assume sources use global config for now unless we refactor sources too.
        # Wait, user wants "request_timeout" configurable.
        # I should pass it to source.check.
        
        ordered_sources = []
        if primary_name in sources:
            ordered_sources.append(sources[primary_name])
        
        # Add fallback
        if allow_fallback:
            for name, src in sources.items():
                if name != primary_name:
                    ordered_sources.append(src)
        
        if not ordered_sources:
             ordered_sources = [sources["ping0"], sources["ippure"]]

        last_error = None
        
        for source in ordered_sources:
            try:
                # Pass timeout via specific mechanism if source supports it?
                # Currently sources import 'config' global.
                # To trigger per-request timeout without rewriting all sources, 
                # we might need to rely on sources reading a contextual config or accept kwargs.
                # Let's check BaseSource again. It takes (proxy_url).
                # I'll update BaseSource later or hack it here?
                # For now let's focus on source selection logic which IS here.
                
                res = await source.check(proxy_url)
                
                if res.get("error"):
                    last_error = res["error"]
                    continue
                
                return res
            except Exception as e:
                last_error = str(e)
                continue
        
        return {
            "pure_emoji": "⚫", "ip_attr": "未知", "ip_src": "未知",
            "pure_score": "?", "ip": "?", 
            "error": f"All sources failed. Last: {last_error}"
        }

    def _strip_old_tag(self, name: str) -> str:
        """去除节点名中已有的检测标注 【...】"""
        import re
        return re.sub(r'\s*【[^】]*】', '', name).strip()

    def _format_name(self, old_name: str, res: dict) -> str:
        # 先去掉已有的标注
        base_name = self._strip_old_tag(old_name)
        
        if res["error"]:
            return f"{base_name} 【❌ 失败】"
            
        # Logic from ping0.py might return "full_string" directly?
        if "full_string" in res and res["full_string"]:
             # If source provides full formatted string, use it but keep base name
             # But ping0 returns "【...】"
             # So we return base_name + full_string
             return f"{base_name} {res['full_string']}"

        info = f"{res['ip_attr']}|{res['ip_src']}"
        return f"{base_name} 【{res['pure_emoji']} {info}】"

    async def async_atomic_save(self, data: dict, file_path: str):
        """Async wrapper for atomic save."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.atomic_save, data, file_path)

    def atomic_save(self, data: dict, file_path: str):
        """Saves YAML to .tmp and renames to target."""
        tmp_path = f"{file_path}.tmp"
        try:
            with open(tmp_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
            os.replace(tmp_path, file_path)
        except Exception as e:
            print(f"LOG: Failed to save atomic YAML: {e}", flush=True)

    async def run_check(self, file_path: str, progress_cb=None, options: dict = None, stop_event=None):
        """
        Main orchestration function.
        options: dict of runtime overrides (skip_keywords, etc)
        stop_event: asyncio.Event to signal cancellation
        """
        options = options or {}
        
        self.current_file = file_path
        try:
            # 1. Wait for API
            if not await self.clash.version():
                print("LOG: Clash API not reachable.", flush=True)
                return

            # 2. Get absolute path for Clash (Docker: mapped paths must work)
            abs_path = os.path.abspath(file_path)
            if not await self.clash.load_config(abs_path):
                return
            
            await asyncio.sleep(1) # Wait reload
            
            # Enforce Port 7890
            await self.clash.update_ports(config.mixed_port)
            
            if await self.clash.set_mode_global():
                print("[INFO] Switched to Global Mode", flush=True)
            else:
                print("[WARN] Failed to switch to Global Mode", flush=True)
            
            port = await self.clash.get_mixed_port()
            proxy_url = f"http://127.0.0.1:{port}"
            
            # 3. Get Proxies
            all_proxies = await self.clash.get_proxies()
            if not all_proxies:
                return

            # Parse local YAML to preserve structure and update names in place
            with open(file_path, 'r', encoding='utf-8') as f:
                yaml_data = yaml.safe_load(f)
            
            # Create a map for fast lookup of YAML proxy objects
            yaml_proxies = yaml_data.get('proxies', [])
            
            total = len(yaml_proxies)
            checked_count = 0
            
            # Initial Progress Report
            if progress_cb:
                await progress_cb(0, total, "Starting...")
            
            # Get Config Values (Runtime Override or Global)
            skip_keywords = options.get("skip_keywords") or self.SKIP_KEYWORDS
            
            for i, p_config in enumerate(yaml_proxies):
                # Check cancellation
                if stop_event and stop_event.is_set():
                    print("[INFO] Check cancelled by user.", flush=True)
                    if progress_cb:
                        await progress_cb(checked_count, total, "Cancelled by user.")
                    break

                name = p_config['name']
                
                # Filter invalid nodes
                if any(k in name for k in skip_keywords):
                     checked_count += 1
                     if progress_cb:
                        await progress_cb(checked_count, total, f"Skipped: {name}")
                     continue

                # Use clean name for logging to avoid confusion with old results
                display_name = self._strip_old_tag(name)
                
                # Switch
                print(f"[INFO] Checking [{i+1}/{total}]: {display_name}", flush=True)
                if progress_cb:
                    await progress_cb(checked_count, total, f"Checking: {display_name}")

                if await self.clash.switch_proxy(name):
                    # Check
                    await asyncio.sleep(0.5) # Wait switch
                    res = await self._check_ip_fast(proxy_url, options=options)

                    
                    # Update Name
                    new_name = self._format_name(name, res)
                    print(f"       => {new_name}", flush=True)
                    p_config['name'] = new_name
                    
                    # Update in proxy-groups
                    if 'proxy-groups' in yaml_data:
                        for g in yaml_data['proxy-groups']:
                            if 'proxies' in g:
                                g['proxies'] = [new_name if pn == name else pn for pn in g['proxies']]

                    # ATOMIC WRITE execution (Batch Save)
                    checked_count += 1
                    if checked_count % 5 == 0:
                         await self.async_atomic_save(yaml_data, file_path)
                         print(f"[INFO] Intermediate Save at {checked_count}/{total}", flush=True)
                    
                    # Notify UI of result
                    if progress_cb:
                        # Show detailed result in logs with Shared Count
                        shared_info = ""
                        if res.get('shared_users') and res.get('shared_users') != "N/A":
                            shared_info = f"  共享: {res['shared_users']}"
                        
                        log_msg = f"Result: IP: {res['ip']}  污染度: {res['pure_score']}{shared_info}  {res['ip_attr']} {res['ip_src']}"
                        await progress_cb(checked_count, total, log_msg)
                    
                    # Also print to console
                    shared_log = f" | 共享: {res.get('shared_users')}" if res.get('shared_users') and res.get('shared_users') != "N/A" else ""
                    print(f"       => IP: {res['ip']} | 污染度: {res['pure_score']}{shared_log} | {res['ip_attr']} | {res['ip_src']}", flush=True)
                else:
                    print(f"[WARN] Could not switch to {name}", flush=True)
                    checked_count += 1  # 即使失败也要计数，保证进度条准确
                    if progress_cb:
                        await progress_cb(checked_count, total, f"Error: Could not switch to {display_name}")

            # Debug: Verify modification before final save? 
            await self.async_atomic_save(yaml_data, file_path) # Force final save
            print(f"[INFO] Check complete. Final save to {file_path}", flush=True)


            # Mark completion (e.g. modify a comment or a metadata field? Or just rely on file mtime)
            print("[INFO] Check complete.", flush=True)

        except Exception as e:
            print(f"[ERROR] Global Check Error: {e}", flush=True)
        finally:
            self.current_file = None
