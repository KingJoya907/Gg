import aiohttp
import asyncio
import configparser
import random
from re import search, compile
from datetime import datetime
from aiohttp_socks import ProxyConnector

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
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

def read_config():
    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8')
    try:
        sources = [s.strip() for s in config['SOCKS5']['Sources'].splitlines() if s.strip()]
        return sources
    except:
        log("ERROR: Failed to read config.ini")
        exit(1)

class RealBrowserBot:
    def __init__(self, channel, post, concurrency=50):  # کمتر برای شبیه‌سازی واقعی
        self.channel = channel
        self.post = post
        self.concurrency = concurrency
        self.semaphore = asyncio.Semaphore(concurrency)
        self.stats = {'total': 0, 'success': 0}
        
    async def send_like_real_browser(self, proxy):
        """ویو زدن مثل یک کاربر واقعی"""
        try:
            async with self.semaphore:
                # تأخیر رندوم شبیه انسان
                await asyncio.sleep(random.uniform(1, 3))
                
                connector = ProxyConnector.from_url(f"socks5://{proxy}")
                
                # Cookie jar مخصوص
                jar = aiohttp.CookieJar(unsafe=True)
                
                # User Agent شبیه مرورگر واقعی
                ua = random.choice([
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
                ])
                
                async with aiohttp.ClientSession(cookie_jar=jar, connector=connector) as session:
                    # ===== مرحله ۱: بازدید از صفحه =====
                    headers1 = {
                        'User-Agent': ua,
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                        'Sec-Fetch-Dest': 'document',
                        'Sec-Fetch-Mode': 'navigate',
                        'Sec-Fetch-Site': 'none',
                        'Sec-Fetch-User': '?1',
                        'Cache-Control': 'max-age=0',
                    }
                    
                    # بازدید از صفحه اصلی پست
                    await session.get(
                        f"https://t.me/{self.channel}/{self.post}",
                        headers=headers1,
                        timeout=10
                    )
                    
                    # تأخیر شبیه انسان
                    await asyncio.sleep(random.uniform(0.5, 1.5))
                    
                    # ===== مرحله ۲: درخواست embed =====
                    headers2 = {
                        'User-Agent': ua,
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Connection': 'keep-alive',
                        'Referer': f'https://t.me/{self.channel}/{self.post}',
                        'Sec-Fetch-Dest': 'iframe',
                        'Sec-Fetch-Mode': 'navigate',
                        'Sec-Fetch-Site': 'same-origin',
                    }
                    
                    async with session.get(
                        f"https://t.me/{self.channel}/{self.post}?embed=1",
                        headers=headers2,
                        timeout=10
                    ) as resp:
                        html = await resp.text()
                        
                        # پیدا کردن توکن
                        token_match = search(r'data-view="([^"]+)"', html)
                        if not token_match:
                            return
                        
                        token = token_match.group(1)
                        
                        # تأخیر شبیه انسان
                        await asyncio.sleep(random.uniform(0.3, 0.8))
                        
                        # ===== مرحله ۳: ارسال ویو =====
                        headers3 = {
                            'User-Agent': ua,
                            'Accept': '*/*',
                            'Accept-Language': 'en-US,en;q=0.5',
                            'Accept-Encoding': 'gzip, deflate, br',
                            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                            'X-Requested-With': 'XMLHttpRequest',
                            'Origin': 'https://t.me',
                            'Connection': 'keep-alive',
                            'Referer': f'https://t.me/{self.channel}/{self.post}?embed=1',
                            'Sec-Fetch-Dest': 'empty',
                            'Sec-Fetch-Mode': 'cors',
                            'Sec-Fetch-Site': 'same-origin',
                        }
                        
                        async with session.post(
                            "https://t.me/v/",
                            params={"views": token},
                            headers=headers3,
                            timeout=10
                        ) as view_resp:
                            
                            self.stats['total'] += 1
                            
                            if view_resp.status == 200:
                                text = await view_resp.text()
                                if text == "true":
                                    self.stats['success'] += 1
                                    log(f"✅ REAL VIEW! با {proxy}")
                                    
                                    # ذخیره پروکسی‌های موفق
                                    with open('working_proxies.txt', 'a') as f:
                                        f.write(f"{proxy}\n")
                            
                            # تأخیر طولانی بین ویوها
                            await asyncio.sleep(random.uniform(5, 10))
                            
        except Exception as e:
            pass
    
    async def worker(self, proxy):
        """کارگر با تأخیرهای طولانی"""
        while True:
            await self.send_like_real_browser(proxy)
    
    async def run(self):
        # اسکرپ پروکسی
        sources = read_config()
        all_proxies = []
        
        for source in sources:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(source, timeout=10) as resp:
                        html = await resp.text()
                        matches = REGEX.finditer(html)
                        proxies = [m.group(1) for m in matches]
                        all_proxies.extend(proxies)
                        log(f"Found {len(proxies)} proxies")
            except:
                pass
        
        log(f"Total proxies: {len(all_proxies)}")
        
        # شروع workerها با concurrency پایین
        workers = min(self.concurrency, len(all_proxies))
        tasks = []
        for i in range(workers):
            task = asyncio.create_task(self.worker(all_proxies[i]))
            tasks.append(task)
        
        log(f"Started {workers} workers - REAL BROWSER MODE")
        
        # نمایش آمار
        while True:
            await asyncio.sleep(10)
            print("\n" + "="*60)
            print(f" 📊 REAL VIEWS: {self.stats['success']}")
            print(f" 📈 TOTAL: {self.stats['total']}")
            print("="*60)
        
        await asyncio.gather(*tasks)

async def main():
    print("\n" + "="*60)
    print(" 🌍 REAL BROWSER SIMULATION MODE 🌍".center(60))
    print("="*60)
    
    url = input(" URL: ").replace('https://t.me/', '').strip()
    channel, post = url.split('/')
    
    print("\n [✓] REAL BROWSER MODE - ویو زدن مثل انسان")
    print(" [⚠️] این روش کندتر ولی واقعی‌تره")
    
    bot = RealBrowserBot(channel, int(post), concurrency=20)  # خیلی کمتر
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())
