import aiohttp
import asyncio
import configparser
import random
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
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (iPad; CPU OS 17_1_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1'
        ]
        
    async def send_view(self, proxy: str):
        """Send view with proxy - با ۳ بار تلاش"""
        try:
            async with self.semaphore:
                connector = ProxyConnector.from_url(f"socks5://{proxy}")
                jar = aiohttp.CookieJar(unsafe=True)
                
                # انتخاب رندوم User Agent
                ua = random.choice(self.user_agents)
                
                async with aiohttp.ClientSession(cookie_jar=jar, connector=connector) as session:
                    # ========== مرحله ۱: دریافت توکن ==========
                    try:
                        async with session.get(
                            f"https://t.me/{self.channel}/{self.post}?embed=1&mode=tme",
                            headers={
                                "referer": f"https://t.me/{self.channel}/{self.post}",
                                "user-agent": ua,
                                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                                "accept-language": "en-US,en;q=0.5",
                                "accept-encoding": "gzip, deflate, br",
                                "connection": "keep-alive",
                                "upgrade-insecure-requests": "1",
                                "sec-fetch-dest": "iframe",
                                "sec-fetch-mode": "navigate",
                                "sec-fetch-site": "same-origin"
                            },
                            timeout=aiohttp.ClientTimeout(total=10),
                        ) as embed_response:
                            
                            if embed_response.status != 200:
                                self.stats['failed'] += 1
                                self.stats['total'] += 1
                                return
                            
                            html = await embed_response.text()
                            
                            # روش‌های مختلف پیدا کردن توکن
                            views_token = None
                            
                            # روش 1: data-view
                            views_token = search('data-view="([^"]+)"', html)
                            
                            # روش 2: data-view بعد از onclick
                            if not views_token:
                                views_token = search('onclick="return viewTelegramWidget\\(([^)]+)\\)', html)
                            
                            # روش 3: توی اسکریپت
                            if not views_token:
                                views_token = search('"viewToken":"([^"]+)"', html)
                            
                            if not views_token:
                                self.stats['failed'] += 1
                                self.stats['total'] += 1
                                return
                            
                            token = views_token.group(1)
                            
                            # ========== مرحله ۲: ارسال ویو ==========
                            async with session.post(
                                "https://t.me/v/",
                                params={"views": token},
                                headers={
                                    "referer": f"https://t.me/{self.channel}/{self.post}?embed=1&mode=tme",
                                    "user-agent": ua,
                                    "x-requested-with": "XMLHttpRequest",
                                    "accept": "*/*",
                                    "accept-language": "en-US,en;q=0.5",
                                    "accept-encoding": "gzip, deflate, br",
                                    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                                    "origin": "https://t.me",
                                    "connection": "keep-alive",
                                    "sec-fetch-dest": "empty",
                                    "sec-fetch-mode": "cors",
                                    "sec-fetch-site": "same-origin"
                                },
                                timeout=aiohttp.ClientTimeout(total=10),
                            ) as view_response:
                                
                                self.stats['total'] += 1
                                
                                if view_response.status == 200:
                                    text = await view_response.text()
                                    if text == "true":
                                        self.stats['success'] += 1
                                        if self.stats['success'] % 10 == 0:
                                            log(f"✅ View #{self.stats['success']} sent with {proxy}")
                                    else:
                                        self.stats['failed'] += 1
                                else:
                                    self.stats['failed'] += 1
                    
                    except asyncio.TimeoutError:
                        self.stats['failed'] += 1
                        self.stats['total'] += 1
                    except Exception as e:
                        self.stats['failed'] += 1
                        self.stats['total'] += 1
                                
        except Exception:
            self.stats['failed'] += 1
            self.stats['total'] += 1
    
    async def worker(self, proxy):
        """هر پروکسی تا وقتی کار میکنه ویو میزنه"""
        views = 0
        consecutive_failures = 0
        max_failures = 5
        
        while self.running and consecutive_failures < max_failures:
            try:
                await self.send_view(proxy)
                views += 1
                
                # اگه ویو موفق بود
                if self.stats['success'] > 0:
                    consecutive_failures = 0
                
                # نمایش گزارش هر ۲۰ ویو
                if views % 20 == 0:
                    log(f"Proxy {proxy} sent {views} views")
                
                await asyncio.sleep(0.3)  # Delay بین ویوها
                
            except Exception:
                consecutive_failures += 1
                await asyncio.sleep(1)
        
        log(f"Proxy {proxy} stopped after {views} views")
    
    async def print_stats(self):
        """آمار لحظه‌ای"""
        last_success = 0
        while self.running:
            await asyncio.sleep(2)
            
            # محاسبه سرعت
            success_rate = (self.stats['success'] / self.stats['total'] * 100) if self.stats['total'] > 0 else 0
            
            print("\n" + "="*60)
            print(" 🚀 TELEGRAM VIEW BOT - FIXED VERSION 🚀".center(60))
            print("="*60)
            print(f" 📊 TARGET: @{self.channel}/{self.post}")
            print(f" 📈 STATISTICS:")
            print(f"    • Total Views: {self.stats['total']:,}")
            print(f"    • Successful: {self.stats['success']:,}")
            print(f"    • Failed: {self.stats['failed']:,}")
            print(f"    • Success Rate: {success_rate:.1f}%")
            print(f" 🔧 SYSTEM:")
            print(f"    • Concurrency: {self.concurrency}")
            print("="*60)
    
    async def run(self):
        """اجرای اصلی"""
        # اسکرپ پروکسی
        scraper = ProxyScraper()
        all_proxies = await scraper.scrape_all()
        
        if not all_proxies:
            log("No proxies found!")
            return
        
        log(f"Starting view sending with {len(all_proxies)} proxies...")
        
        # شروع آمار
        asyncio.create_task(self.print_stats())
        
        # شروع workerها
        workers_count = min(self.concurrency, len(all_proxies))
        tasks = []
        
        # پخش کردن پروکسی‌ها بین workerها
        for i in range(workers_count):
            proxy = all_proxies[i]
            task = asyncio.create_task(self.worker(proxy))
            tasks.append(task)
        
        log(f"Started {workers_count} workers")
        await asyncio.gather(*tasks, return_exceptions=True)

# ==================== Main ====================
async def main():
    print("\n" + "="*60)
    print(" 🚀 TELEGRAM VIEW BOT - ULTIMATE FIXED VERSION 🚀".center(60))
    print("="*60)
    
    url = input("\n Enter Telegram View Post URL: ").replace('https://t.me/', '').strip()
    if '/' not in url:
        print(" Invalid URL!")
        return
    
    channel, post = url.split('/')
    print(f"\n [✓] Channel: @{channel}")
    print(f" [✓] Post ID: {post}")
    
    try:
        cc = int(input("\n Enter concurrency (default 1000): ") or "1000")
    except:
        cc = 1000
    
    print("\n" + "="*60)
    print(" 🚀 Starting bot - با قابلیت ویو زدن پیشرفته...")
    print("="*60 + "\n")
    
    bot = TelegramViewBot(channel, int(post), cc)
    await bot.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n [👋] Bot stopped by user")
    except Exception as e:
        print(f"\n [❌] Error: {str(e)}")
