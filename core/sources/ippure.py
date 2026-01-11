from .base import BaseSource
from curl_cffi.requests import AsyncSession
from ..config import config

class IPPureSource(BaseSource):
    @property
    def name(self) -> str:
        return "ippure"

    async def check(self, proxy_url: str) -> dict:
        url = config.check_url # Default: https://my.123169.xyz/v1/info (Mirror of IPPure)
        
        result = {
            "pure_emoji": "⚪", "ip_attr": "未知", "ip_src": "未知",
            "pure_score": "?", "ip": "?", "error": None
        }
        
        proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None

        try:
            async with AsyncSession(proxies=proxies, impersonate="chrome110", timeout=5) as session:
                resp = await session.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    
                    result["ip"] = data.get("ip", "❓")
                    
                    # Score
                    f_score = data.get("fraudScore")
                    if f_score is not None:
                       result["pure_score"] = f"{f_score}%"
                       result["pure_emoji"] = self.get_emoji(result["pure_score"])

                    # Attr
                    if data.get("isResidential"): result["ip_attr"] = "住宅"
                    else: result["ip_attr"] = "机房"
                    
                    # Source
                    if data.get("isBroadcast"): result["ip_src"] = "广播"
                    else: result["ip_src"] = "原生"
                else:
                    result["error"] = f"HTTP {resp.status_code}"

        except Exception as e:
            result["error"] = str(e)
            
        return result
