import aiohttp
import urllib.parse
import json
import logging

# Configure logging
# logging.basicConfig removed to allow main.py to control config
logger = logging.getLogger("ClashAPI")

class ClashController:
    def __init__(self, api_url, secret=""):
        self.api_url = api_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {secret}",
            "Content-Type": "application/json"
        }

    async def version(self):
        """Checks API availability."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/version", headers=self.headers, timeout=5) as resp:
                    return resp.status == 200
        except Exception:
            return False

    async def load_config(self, file_path: str):
        """
        Loads a config by file path.
        Note: The path must be accessible BY the Clash process (inside Docker container).
        """
        url = f"{self.api_url}/configs"
        # Force allow-lan to true to ensure we can connect from outside if needed, 
        # but key is ensuring mode 'global'
        payload = {"path": file_path} 
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.put(url, json=payload, headers=self.headers, timeout=30) as resp:
                    if resp.status == 204:
                        print(f"[INFO] Loaded config: {file_path}", flush=True)
                        await self.set_log_level("error")
                        return True
                    else:
                        text = await resp.text()
                        print(f"[ERROR] Failed to load config {file_path}: {resp.status} - {text}", flush=True)
                        return False
        except Exception as e:
            print(f"[ERROR] API Error loading config: {type(e).__name__}: {e}", flush=True)
            return False

    async def set_mode_global(self):
        """Sets Clash to Global mode."""
        url = f"{self.api_url}/configs"
        payload = {"mode": "global"}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.patch(url, json=payload, headers=self.headers, timeout=5) as resp:
                    return resp.status == 204
        except Exception as e:
            print(f"[ERROR] Error setting global mode: {e}", flush=True)
            return False

    async def set_log_level(self, level="error"):
        """Sets the log level."""
        url = f"{self.api_url}/configs"
        payload = {"log-level": level}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.patch(url, json=payload, headers=self.headers, timeout=5) as resp:
                    return resp.status == 204
        except Exception as e:
            print(f"[ERROR] Error setting log level: {e}", flush=True)
            return False

    async def get_proxies(self):
        """Fetches all proxies."""
        try:
             async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/proxies", headers=self.headers, timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get('proxies', {})
        except Exception as e:
            print(f"[ERROR] Error fetching proxies: {e}", flush=True)
            return None

    async def switch_proxy(self,  proxy_name):
        """Switches the GLOBAL selector to the specified proxy."""
        # For Global mode, we usually select the node in the 'GLOBAL' selector or equivalent.
        # But in pure Global mode, there is usually a selector named 'GLOBAL' (or similar).
        # We try 'GLOBAL' first.
        selector = "GLOBAL"
        url = f"{self.api_url}/proxies/{urllib.parse.quote(selector)}"
        payload = {"name": proxy_name}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.put(url, json=payload, headers=self.headers, timeout=5) as resp:
                    if resp.status == 204:
                        return True
                    else:
                        # Fallback: maybe the selector isn't GLOBAL? 
                        # But standard Clash Global mode uses GLOBAL selector.
                        print(f"[WARN] Failed to switch {selector} to {proxy_name}. Status: {resp.status}", flush=True)
                        return False
        except Exception as e:
            print(f"[ERROR] API Error switching proxy: {e}", flush=True)
            return False

    async def update_ports(self, port=7890):
        """Forces the mixed-port to be open."""
        url = f"{self.api_url}/configs"
        # We enforce mixed-port. If not supported by old Clash, use 'port' and 'socks-port'.
        # But Mihomo supports mixed-port.
        payload = {"mixed-port": port, "allow-lan": False} 
        try:
            async with aiohttp.ClientSession() as session:
                async with session.patch(url, json=payload, headers=self.headers, timeout=5) as resp:
                    if resp.status == 204:
                        print(f"[INFO] Enforced mixed-port: {port}", flush=True)
                        return True
                    else:
                        print(f"[WARN] Failed to enforce ports: {resp.status}", flush=True)
                        return False
        except Exception as e:
            print(f"[ERROR] API Error updating ports: {e}", flush=True)
            return False

    async def get_mixed_port(self):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/configs", headers=self.headers, timeout=5) as resp:
                    if resp.status == 200:
                        conf = await resp.json()
                        return conf.get('mixed-port') or conf.get('port') or 7890
        except:
            return 7890
