import aiohttp
import asyncio
import configparser
from re import search, compile
from datetime import datetime
from fake_useragent import UserAgent
from aiohttp_socks import ProxyConnector

# ==================== REGEX for proxy extraction ====================
REGEX = compile(
    r"(?:^|\D)?(("+ r"(?:[1-9]|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
    + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
    + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
    + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
    + r"):" + (r"(?:\d|[1-9]\d{1,3}|[1-5]\d{4}|6[0-4]\d{3}"
    + r"|65[0-4]\d{2}|655[0-2]\d|6553[0-5])")
    + r")(?:\D|$)"
)

def log(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

# ==================== Read config.ini ====================
def read_config():
    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8')
    
    try:
        socks5_sources = config['SOCKS5']['Sources'].splitlines()
        # Remove empty lines and strip whitespace
        sources = [s.strip() for s in socks5_sources if s.strip()]
        log(f"Loaded {len(sources)} proxy sources from config.ini")
        return sources
    except Exception as e:
        log(f"ERROR: Failed to read config.ini - {str(e)}")
        exit(1)

# ==================== Proxy Scraper ====================
class ProxyScraper:
    def __init__(self):
        self.proxies = []
        self.sources = read_config()
        
    async def scrape_source(self, source_url):
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"user-agent": UserAgent().random}
                async with session.get(
                    source_url, 
                    headers=headers, 
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    html = await response.text()
                    matches = REGEX.finditer(html)
                    found_proxies = [match.group(1) for match in matches]
                    self.proxies.extend(found_proxies)
                    log(f"Found {len(found_proxies)} proxies from {source_url[:50]}...")
        except Exception as e:
            log(f"Failed to scrape {source_url[:50]}... - {str(e)[:50]}")
    
    async def scrape_all(self):
        log("Starting proxy scraping from config.ini sources...")
        tasks = [self.scrape_source(source) for source in self.sources]
        await asyncio.gather(*tasks)
        log(f"Scraping complete! Total proxies: {len(self.proxies)}")
        return self.proxies

# ==================== Telegram View Bot ====================
class TelegramViewBot:
    def __init__(self, channel: str, post: int, concurrency: int = 500):
        self.channel = channel
        self.post = post
        self.concurrency = concurrency
        self.semaphore = asyncio.Semaphore(concurrency)
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'proxy_errors': 0,
            'token_errors': 0
        }
        self.running = True
        self.working_proxies = []  # Will store tested working proxies
        
    async def test_proxy(self, proxy):
        """Test if proxy is working"""
        try:
            connector = ProxyConnector.from_url(f"socks5://{proxy}")
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(
                    "http://httpbin.org/ip",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    return response.status == 200
        except:
            return False
    
    async def filter_working_proxies(self, proxies):
        """Test and filter working proxies"""
        log(f"Testing {len(proxies)} proxies (this may take a while)...")
        
        working = []
        tested = 0
        
        for proxy in proxies[:1000]:  # Test first 1000 proxies
            if await self.test_proxy(proxy):
                working.append(proxy)
            tested += 1
            if tested % 100 == 0:
                log(f"Tested {tested}/{min(1000, len(proxies))} proxies - Found {len(working)} working")
        
        log(f"Proxy testing complete! Found {len(working)} working proxies")
        return working
    
    async def send_view(self, proxy: str):
        """Send a single view using proxy"""
        try:
            async with self.semaphore:
                connector = ProxyConnector.from_url(f"socks5://{proxy}")
                jar = aiohttp.CookieJar(unsafe=True)
                
                async with aiohttp.ClientSession(cookie_jar=jar, connector=connector) as session:
                    user_agent = UserAgent().random
                    
                    # Get token
                    async with session.get(
                        f"https://t.me/{self.channel}/{self.post}?embed=1&mode=tme",
                        headers={"referer": f"https://t.me/{self.channel}/{self.post}", "user-agent": user_agent},
                        timeout=aiohttp.ClientTimeout(total=10),
                    ) as embed_response:
                        
                        if not jar.filter_cookies(embed_response.url).get("stel_ssid"):
                            self.stats['token_errors'] += 1
                            self.stats['total'] += 1
                            self.stats['failed'] += 1
                            return
                        
                        html = await embed_response.text()
                        views_token = search('data-view="([^"]+)"', html)
                        
                        if not views_token:
                            self.stats['token_errors'] += 1
                            self.stats['total'] += 1
                            self.stats['failed'] += 1
                            return
                        
                        # Send view
                        async with session.post(
                            "https://t.me/v/?views=" + views_token.group(1),
                            headers={
                                "referer": f"https://t.me/{self.channel}/{self.post}?embed=1&mode=tme",
                                "user-agent": user_agent,
                                "x-requested-with": "XMLHttpRequest",
                            },
                            timeout=aiohttp.ClientTimeout(total=10),
                        ) as view_response:
                            
                            self.stats['total'] += 1
                            
                            if view_response.status == 200 and await view_response.text() == "true":
                                self.stats['success'] += 1
                            else:
                                self.stats['failed'] += 1
                                
        except Exception:
            self.stats['proxy_errors'] += 1
            self.stats['total'] += 1
            self.stats['failed'] += 1
    
    async def worker(self, proxy):
        """Continuous worker for a single proxy"""
        while self.running:
            await self.send_view(proxy)
            await asyncio.sleep(0.5)  # Delay between views
    
    async def print_stats(self):
        """Print statistics every second"""
        while self.running:
            await asyncio.sleep(1)
            success_rate = (self.stats['success'] / self.stats['total'] * 100) if self.stats['total'] > 0 else 0
            
            print("\n" + "="*60)
            print(" 🚀 TELEGRAM VIEW BOT - SOCKS5 ONLY 🚀".center(60))
            print("="*60)
            print(f"\n 📊 TARGET: @{self.channel}/{self.post}")
            print(f"\n 📈 STATISTICS:")
            print(f"    • Total Views: {self.stats['total']:,}")
            print(f"    • Successful: {self.stats['success']:,}")
            print(f"    • Failed: {self.stats['failed']:,}")
            print(f"    • Success Rate: {success_rate:.1f}%")
            print(f"    • Proxy Errors: {self.stats['proxy_errors']}")
            print(f"    • Token Errors: {self.stats['token_errors']}")
            print(f"\n 🔧 SYSTEM:")
            print(f"    • Concurrency: {self.concurrency}")
            print(f"    • Working Proxies: {len(self.working_proxies)}")
            print("="*60)
    
    async def run(self):
        """Main run function"""
        # Scrape proxies from config.ini sources
        scraper = ProxyScraper()
        all_proxies = await scraper.scrape_all()
        
        if not all_proxies:
            log("No proxies found! Exiting...")
            return
        
        # Test and filter working proxies
        self.working_proxies = await self.filter_working_proxies(all_proxies)
        
        if not self.working_proxies:
            log("No working proxies found! Exiting...")
            return
        
        # Start statistics printer
        asyncio.create_task(self.print_stats())
        
        # Start workers with working proxies
        workers_count = min(self.concurrency, len(self.working_proxies))
        log(f"Starting {workers_count} workers with working proxies...")
        
        tasks = []
        for proxy in self.working_proxies[:workers_count]:
            task = asyncio.create_task(self.worker(proxy))
            tasks.append(task)
        
        # Wait for all workers
        await asyncio.gather(*tasks, return_exceptions=True)

# ==================== Main ====================
async def main():
    print("\n" + "="*60)
    print(" 🚀 TELEGRAM VIEW BOT - CONFIG.INI ONLY 🚀".center(60))
    print("="*60)
    print()
    
    # Get target info
    url = input(" Enter Telegram View Post URL: ").replace('https://t.me/', '').strip()
    if '/' not in url:
        print("\n [❌] Invalid URL!")
        return
    
    channel, post = url.split('/')
    print(f"\n [✓] Channel: @{channel}")
    print(f" [✓] Post ID: {post}")
    
    # Get concurrency
    try:
        cc = int(input("\n Enter concurrency (default 500): ") or "500")
    except:
        cc = 500
    
    print("\n" + "="*60)
    print(" 🚀 Starting bot...")
    print("="*60 + "\n")
    
    # Create and run bot
    bot = TelegramViewBot(channel, int(post), cc)
    await bot.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n [👋] Bot stopped by user")
    except Exception as e:
        print(f"\n [❌] Error: {str(e)}")
