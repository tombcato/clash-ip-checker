from abc import ABC, abstractmethod

class BaseSource(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    async def check(self, proxy_url: str, timeout: int = None) -> dict:
        """
        Check IP information using the proxy.
        Returns a dict with format:
        {
            "ip": "1.2.3.4",
            "pure_score": "10%",
            "pure_emoji": "🟢", 
            "ip_attr": "住宅", # or 机房
            "ip_src": "原生", # or 广播
            "error": None
        }
        """
        pass

    def get_emoji(self, percentage_str):
        try:
            val = float(percentage_str.replace('%', ''))
            # Logic from ipcheck.py with user approved thresholds
            if val <= 10: return "⚪"
            if val <= 30: return "🟢"
            if val <= 50: return "🟡"
            if val <= 70: return "🟠"
            if val <= 90: return "🔴"
            return "⚫"
        except Exception:
            return "❓"
