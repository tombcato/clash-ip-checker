import asyncio
import re
import aiohttp
from playwright.async_api import async_playwright

class IPChecker:
    def __init__(self, headless=True):
        self.headless = headless
        self.browser = None
        self.playwright = None
        self.cache = {} # Map IP -> Result Dict

    async def start(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )

    async def stop(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

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
        except:
            return "❓"

    async def get_simple_ip(self, proxy=None):
        """Fast IPv4 check for caching."""
        urls = ["http://api.ipify.org", "http://v4.ident.me", "http://ipinfo.io/ip"]
        
        async def fetch_ip(session, url):
            try:
                async with session.get(url, proxy=proxy) as resp:
                    if resp.status == 200:
                        ip = (await resp.text()).strip()
                        if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", ip):
                            return ip
            except Exception:
                pass
            return None
        
        try:
            timeout = aiohttp.ClientTimeout(total=2)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Try all sources concurrently, return first success
                tasks = [fetch_ip(session, url) for url in urls]
                for coro in asyncio.as_completed(tasks):
                    result = await coro
                    if result:
                        return result
        except Exception:
            pass
        return None
    
    async def get_ip_info_fast(self, ip, proxy=None):
        """Get IP info from fast API (ip-api.com supports batch)."""
        try:
            timeout = aiohttp.ClientTimeout(total=3)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # ip-api.com free tier - no proxy needed for this
                url = f"http://ip-api.com/json/{ip}?fields=status,message,country,isp,org,hosting,proxy"
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get('status') == 'success':
                            # Determine if datacenter/residential
                            is_hosting = data.get('hosting', False)
                            is_proxy = data.get('proxy', False)
                            
                            # Estimate score based on hosting/proxy flags
                            if is_hosting and is_proxy:
                                score = 75
                            elif is_hosting:
                                score = 50
                            elif is_proxy:
                                score = 40
                            else:
                                score = 15
                            
                            ip_type = "机房" if is_hosting else "住宅"
                            ip_src = "代理" if is_proxy else "原生"
                            
                            return {
                                "ip": ip,
                                "pure_score": f"{score}%",
                                "pure_emoji": self.get_emoji(f"{score}%"),
                                "bot_score": f"{score * 0.5:.1f}%",
                                "bot_emoji": self.get_emoji(f"{score * 0.5:.1f}%"),
                                "ip_attr": ip_type,
                                "ip_src": ip_src,
                                "country": data.get('country', 'Unknown'),
                                "isp": data.get('isp', 'Unknown'),
                                "full_string": f"【{self.get_emoji(f'{score}%')}{self.get_emoji(f'{score * 0.5:.1f}%')} {ip_type}|{ip_src}】",
                                "error": None,
                                "fast_check": True
                            }
        except Exception as e:
            pass
        return None

    async def check(self, url="https://ippure.com/", proxy=None, timeout=15000, fast_mode=True, skip_browser=False):
        if not self.browser:
            await self.start()
        
        # 1. Cleaner Fast IP & Cache Logic
        current_ip = await self.get_simple_ip(proxy)
        if current_ip and current_ip in self.cache:
            print(f"     [Cache Hit] {current_ip}", flush=True)
            return self.cache[current_ip]
        
        if current_ip:
            print(f"     [New IP] {current_ip}", flush=True)
            
            # Try fast API check first (much faster than browser)
            if fast_mode:
                fast_result = await self.get_ip_info_fast(current_ip, proxy)
                if fast_result:
                    print(f"     [Fast API] Score: {fast_result['pure_score']}", flush=True)
                    self.cache[current_ip] = fast_result
                    return fast_result
        else:
            # Fast IP check failed - node may be unreachable
            if skip_browser:
                print("     [Skip] Node unreachable, skipping browser check...", flush=True)
                return {"skipped": True, "error": "Fast IP check failed"}
            print("     [Warning] Fast IP check failed. Scanning with browser...", flush=True)

        # 2. Browser Check (Logic from ipcheck.py)
        context_args = {
             "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        if proxy:
            context_args["proxy"] = {"server": proxy}
            
        context = await self.browser.new_context(**context_args)
        
        # Resource blocking (Optimization)
        await context.route("**/*", lambda route: route.abort() 
            if route.request.resource_type in ["image", "media", "font"] 
            else route.continue_())

        page = await context.new_page()
        
        # Default Result Structure
        result = {
            "pure_emoji": "❓", "bot_emoji": "❓", "ip_attr": "❓", "ip_src": "❓",
            "pure_score": "❓", "bot_score": "❓", "full_string": "", "ip": current_ip if current_ip else "❓", "error": None
        }

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout)
            
            # Logic from ipcheck.py - Optimized wait
            try:
                await page.wait_for_selector("text=人机流量比", timeout=6000)
            except:
                pass 

            await page.wait_for_timeout(500)
            text = await page.inner_text("body")

            # 1. IPPure Score
            score_match = re.search(r"IPPure系数.*?(\d+%)", text, re.DOTALL)
            if score_match:
                result["pure_score"] = score_match.group(1)
                result["pure_emoji"] = self.get_emoji(result["pure_score"])

            # 2. Bot Ratio
            bot_match = re.search(r"bot\s*(\d+(\.\d+)?)%", text, re.IGNORECASE)
            if bot_match:
                val = bot_match.group(0).replace('bot', '').strip()
                if not val.endswith('%'): val += "%"
                result["bot_score"] = val
                result["bot_emoji"] = self.get_emoji(val)

            # 3. Attributes
            attr_match = re.search(r"IP属性\s*\n\s*(.+)", text)
            if not attr_match: attr_match = re.search(r"IP属性\s*(.+)", text)
            if attr_match:
                raw = attr_match.group(1).strip()
                result["ip_attr"] = re.sub(r"IP$", "", raw)

            # 4. Source
            src_match = re.search(r"IP来源\s*\n\s*(.+)", text)
            if not src_match: src_match = re.search(r"IP来源\s*(.+)", text)
            if src_match:
                raw = src_match.group(1).strip()
                result["ip_src"] = re.sub(r"IP$", "", raw)

            # 5. Fallback IP if fast check failed
            if result["ip"] == "❓":
                ip_match = re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", text)
                if ip_match: result["ip"] = ip_match.group(0)

            # Construct String with user requested '|' separator
            attr = result["ip_attr"] if result["ip_attr"] != "❓" else ""
            src = result["ip_src"] if result["ip_src"] != "❓" else ""
            info = f"{attr}|{src}".strip()
            if info == "|": info = "未知" # Handle empty case gracefully
            if not info: info = "未知"
            
            result["full_string"] = f"【{result['pure_emoji']}{result['bot_emoji']} {info}】"

            # Cache Update
            if result["ip"] != "❓" and result["pure_score"] != "❓":
                self.cache[result["ip"]] = result.copy()

        except Exception as e:
            result["error"] = str(e)
            result["full_string"] = "【❌ Error】"
        finally:
            if not self.headless:
                print("     [Debug] Waiting 5s before closing browser window...")
                await asyncio.sleep(5)
            await page.close()
            await context.close()
            
        return result
