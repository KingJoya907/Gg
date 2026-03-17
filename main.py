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
        sources = [s.strip() for s in socks5_sources if s.strip()]
        log(f"Loaded {len(sources)} proxy sources")
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
                async with session.get(source_url, timeout=15) as response:
                    html = await response.text()
                    matches = REGEX.finditer(html)
                    found_proxies = [match.group(1) for match in matches]
                    self.proxies.extend(found_proxies)
                    log(f"Found {len(found_proxies)} proxies from {source_url[:40]}...")
        except Exception as e:
            log(f"Failed to scrape {source_url[:40]}...")
    
    async def scrape_all(self):
        log("Scraping proxies...")
        tasks = [self.scrape_source(source) for source in self.sources]
        await asyncio.gather(*tasks)
        log(f"Total proxies: {len(self.proxies)}")
        return self.proxies

# ==================== Telegram View Bot ====================
class TelegramViewBot:
    def __init__(self, channel: str, post: int, concurrency: int = 1000):
        self.channel = channel
        self.post = post
        self.concurrency = concurrency
        self.semaphore = asyncio.Semaphore(concurrency)
        self.stats = {'total': 0, 'success': 0, 'failed': 0}
        self.running = True
        
    async def send_view(self, proxy: str):
        """Send view with proxy - اگر کار کرد ثبت میشه"""
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
                        
                        html = await embed_response.text()
                        views_token = search('data-view="([^"]+)"', html)
                        
                        if not views_token:
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
                                log(f"✅ View #{self.stats['success']} sent with {proxy}")
                            else:
                                self.stats['failed'] += 1
                                
        except Exception:
            self.stats['failed'] += 1
            self.stats['total'] += 1
    
    async def worker(self, proxy):
        """هر پروکسی تا وقتی کار میکنه ویو میزنه"""
        views = 0
        while self.running:
            try:
                await self.send_view(proxy)
                views += 1
                if views % 10 == 0:
                    log(f"Proxy {proxy} sent {views} views")
                await asyncio.sleep(0.5)
            except:
                break
        log(f"Proxy {proxy} stopped after {views} views")
    
    async def print_stats(self):
        """آمار لحظه‌ای"""
        while self.running:
            await asyncio.sleep(2)
            rate = (self.stats['success'] / self.stats['total'] * 100) if self.stats['total'] > 0 else 0
            print("\n" + "="*60)
            print(f" 📊 Views: {self.stats['total']} | ✅ {self.stats['success']} | ❌ {self.stats['failed']} | {rate:.1f}%")
            print("="*60)
    
    async def run(self):
        """اجرای اصلی - مستقیم میره سراغ ویو زدن"""
        # اسکرپ پروکسی
        scraper = ProxyScraper()
        all_proxies = await scraper.scrape_all()
        
        if not all_proxies:
            log("No proxies found!")
            return
        
        log(f"Starting direct view sending with {len(all_proxies)} proxies...")
        
        # شروع آمار
        asyncio.create_task(self.print_stats())
        
        # شروع workerها - بدون تست، مستقیم ویو
        workers_count = min(self.concurrency, len(all_proxies))
        tasks = []
        
        for i in range(workers_count):
            proxy = all_proxies[i % len(all_proxies)]
            task = asyncio.create_task(self.worker(proxy))
            tasks.append(task)
        
        log(f"Started {workers_count} workers - هر کی کار کنه ویو میزنه")
        await asyncio.gather(*tasks, return_exceptions=True)

# ==================== Main ====================
async def main():
    print("\n" + "="*60)
    print(" 🚀 TELEGRAM VIEW BOT - DIRECT MODE 🚀".center(60))
    print("="*60)
    
    url = input(" Enter URL: ").replace('https://t.me/', '').strip()
    channel, post = url.split('/')
    
    cc = int(input(" Concurrency (default 1000): ") or "1000")
    
    print("\n" + "="*60)
    print(" 🚀 Starting - بدون تست، مستقیم ویو...")
    print("="*60 + "\n")
    
    bot = TelegramViewBot(channel, int(post), cc)
    await bot.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n [👋] Bot stopped")
