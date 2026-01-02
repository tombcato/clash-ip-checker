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
        
    async def _check_ip_fast(self, proxy_url: str):
        """
        Checks IP using curl_cffi via the local proxy.
        """
        url = config.check_url
        result = {
            "pure_emoji": "⚪", "ip_attr": "未知", "ip_src": "未知",
            "pure_score": "?", "ip": "?", "error": None
        }
        
        proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None

        try:
            async with AsyncSession(proxies=proxies, impersonate="chrome110", timeout=config.request_timeout) as session:
                resp = await session.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    
                    result["ip"] = data.get("ip", "❓")
                    
                    # Score
                    f_score = data.get("fraudScore")
                    if f_score is not None:
                       result["pure_score"] = f"{f_score}%"
                       # Emoji logic: 0-10% ⚪, else maybe 🟢? Keeping simple as per Fast Mode request
                       if isinstance(f_score, int):
                           if f_score <= 10: result["pure_emoji"] = "⚪"
                           elif f_score <= 30: result["pure_emoji"] = "🟢"
                           elif f_score <= 50: result["pure_emoji"] = "🟡"
                           elif f_score <= 70: result["pure_emoji"] = "🟠"
                           elif f_score <= 90: result["pure_emoji"] = "🔴"
                           else: result["pure_emoji"] = "⚫"

                    # Attr
                    if data.get("isResidential"): result["ip_attr"] = "住宅"
                    else: result["ip_attr"] = "机房"
                    
                    # Source
                    if data.get("isBroadcast"): result["ip_src"] = "广播"
                    else: result["ip_src"] = "原生"
                else:
                    result["error"] = f"HTTP {resp.status_code}"

        except Exception as e:
            print(f"[ERROR] Check failed for : {e}", flush=True)
            result["error"] = str(e)
            
        return result

    def _strip_old_tag(self, name: str) -> str:
        """去除节点名中已有的检测标注 【...】"""
        import re
        # 匹配 【任意内容】 格式的标注，可能有多个
        # 例如: "香港01 【🟢 住宅|原生】" → "香港01"
        # 例如: "日本02 【❌ 失败】" → "日本02"
        return re.sub(r'\s*【[^】]*】', '', name).strip()

    def _format_name(self, old_name: str, res: dict) -> str:
        # 先去掉已有的标注
        base_name = self._strip_old_tag(old_name)
        
        if res["error"]:
            return f"{base_name} 【❌ 失败】"
            
        info = f"{res['ip_attr']}|{res['ip_src']}"
        return f"{base_name} 【{res['pure_emoji']} {info}】"

    def atomic_save(self, data: dict, file_path: str):
        """Saves YAML to .tmp and renames to target."""
        tmp_path = f"{file_path}.tmp"
        try:
            with open(tmp_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
            os.replace(tmp_path, file_path)
        except Exception as e:
            print(f"LOG: Failed to save atomic YAML: {e}", flush=True)

    async def run_check(self, file_path: str, progress_cb=None):
        """
        Main orchestration function.
        1. Access API
        2. Load Config
        3. Iterate & Check
        4. Update File Atomically
        """
        
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
                yaml_data = yaml.full_load(f)
            
            # Create a map for fast lookup of YAML proxy objects
            yaml_proxies = yaml_data.get('proxies', [])
            
            # Identify testable proxies (from API list)
            # Filter out incompatible types (Selector, URLTest, etc.) happens implicitly by existing check
            # but we iterate the YAML list to maintain order.
            
            total = len(yaml_proxies)
            checked_count = 0
            
            # Initial Progress Report
            if progress_cb:
                await progress_cb(0, total, "Starting...")
            
            for i, p_config in enumerate(yaml_proxies):
                name = p_config['name']
                
                # Filter invalid nodes
                if any(k in name for k in self.SKIP_KEYWORDS):
                     # Still report progress for skipped items?
                     # Let's count them as done for progress bar accuracy?
                     # Or just ignore from total?
                     # Better to increment count but say "Skipped".
                     checked_count += 1
                     if progress_cb:
                        await progress_cb(checked_count, total, f"Skipped: {name}")
                     continue

                # Use full name for logging to avoid confusion
                display_name = name
                
                # Switch
                print(f"[INFO] Checking [{i+1}/{total}]: {display_name}", flush=True)
                if progress_cb:
                    await progress_cb(checked_count, total, f"Checking: {display_name}")

                if await self.clash.switch_proxy(name):
                    # Check
                    await asyncio.sleep(0.5) # Wait switch
                    res = await self._check_ip_fast(proxy_url)
                    
                    # Update Name
                    new_name = self._format_name(name, res)
                    print(f"       => {new_name}", flush=True)
                    p_config['name'] = new_name
                    
                    # Update in proxy-groups
                    if 'proxy-groups' in yaml_data:
                        for g in yaml_data['proxy-groups']:
                            if 'proxies' in g:
                                g['proxies'] = [new_name if pn == name else pn for pn in g['proxies']]

                    # ATOMIC WRITE execution
                    self.atomic_save(yaml_data, file_path)
                    checked_count += 1
                    
                    # Notify UI of result
                    if progress_cb:
                        # Show detailed result in logs
                        log_msg = f"Result: IP: {res['ip']}  污染度: {res['pure_score']}  {res['ip_attr']} {res['ip_src']}"
                        await progress_cb(checked_count, total, log_msg)
                    
                    # 也打印到控制台日志
                    print(f"       => IP: {res['ip']} | 污染度: {res['pure_score']} | {res['ip_attr']} | {res['ip_src']}", flush=True)
                else:
                    print(f"[WARN] Could not switch to {name}", flush=True)
                    checked_count += 1  # 即使失败也要计数，保证进度条准确
                    if progress_cb:
                        await progress_cb(checked_count, total, f"Error: Could not switch to {display_name}")

            # Debug: Verify modification before final save? 
            self.atomic_save(yaml_data, file_path) # Force final save
            print(f"[INFO] Check complete. Final save to {file_path}", flush=True)


            # Mark completion (e.g. modify a comment or a metadata field? Or just rely on file mtime)
            print("[INFO] Check complete.", flush=True)

        except Exception as e:
            print(f"[ERROR] Global Check Error: {e}", flush=True)
        finally:
            self.current_file = None
