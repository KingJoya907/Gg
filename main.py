import aiohttp
import asyncio
import configparser
import random
from re import search, compile
from aiohttp_socks import ProxyConnector
import logging
import time
import sys
from datetime import datetime

logging.basicConfig(level=logging.INFO)

# لیست User-Agent واقعی
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 15; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.6668.71 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
]

REGEX = compile(
    r"(?:^|\D)?(("
    r"(?:[1-9]|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
    r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
    r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
    r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
    r"):" + r"(?:\d|[1-9]\d{1,3}|[1-5]\d{4}|6[0-4]\d{3}"
    r"|65[0-4]\d{2}|655[0-2]\d|6553[0-5])"
    r")(?:\D|$)"
)

# ==================== خواندن config.ini ====================
def read_config():
    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8')
    
    sources = []
    if 'SOCKS5' in config:
        sources = [s.strip() for s in config['SOCKS5']['Sources'].splitlines() if s.strip()]
        print(f" [✓] Found {len(sources)} proxy sources")
    else:
        print(" [❌] SOCKS5 section not found!")
        print(" Creating default config.ini...")
        with open('config.ini', 'w', encoding='utf-8') as f:
            f.write("""[SOCKS5]
Sources = 
    https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt
    https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks5.txt
    https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS5_RAW.txt
""")
        return read_config()
    
    return sources

# ==================== اسکرپ پروکسی ====================
async def scrape_proxies(sources):
    proxies = set()
    print("\n [*] Scraping proxies...")
    
    async with aiohttp.ClientSession() as session:
        for source in sources:
            try:
                print(f" [*] Fetching: {source[:60]}...")
                async with session.get(source, timeout=12) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        found = [m.group(1) for m in REGEX.finditer(text)]
                        proxies.update(found)
                        print(f" [✓] +{len(found)}")
            except Exception as e:
                print(f" [✗] {str(e)[:40]}")
    
    proxies = list(proxies)
    random.shuffle(proxies)
    print(f"\n [✓] Total unique proxies: {len(proxies)}")
    return proxies

# ==================== کلاس اصلی ویو زدن ====================
class TelegramViews:
    def __init__(self, channel: str, posts: list, views_per_post: int, proxy_list: list):
        self.views_per_post = views_per_post
        self.channel = channel.lstrip('@')
        self.posts = posts
        self.proxy_list = proxy_list
        self.total_views = views_per_post * len(posts)
        
        self.success = 0
        self.failed = 0
        self.proxy_err = 0
        self.token_err = 0
        self.cookie_err = 0
        self.completed = 0
        
        self.start_time = time.time()
        self.proxy_idx = 0

    def progress(self):
        pct = (self.completed / self.total_views) * 100 if self.total_views > 0 else 0
        bar = '█' * int(pct // 2) + '░' * (50 - int(pct // 2))
        elapsed = time.time() - self.start_time
        rate = self.completed / elapsed if elapsed > 0 else 0
        
        print(f"\r[{bar}] {pct:5.1f}% | ✓{self.success:4} | ✗{self.failed:4} | ⚠{self.proxy_err:3} | {rate:5.1f}/s", end='', flush=True)

    def next_proxy(self):
        if not self.proxy_list:
            return None
        p = self.proxy_list[self.proxy_idx % len(self.proxy_list)]
        self.proxy_idx += 1
        return p

    async def view_post(self, post: int, max_retries=3):
        proxy = self.next_proxy()
        if not proxy:
            self.proxy_err += 1
            self.completed += 1
            self.progress()
            return

        ua = random.choice(USER_AGENTS)
        referer = f"https://t.me/{self.channel}/{post}"

        connector = ProxyConnector.from_url(f'socks5://{proxy}', rdns=True)
        
        for attempt in range(max_retries):
            try:
                jar = aiohttp.CookieJar(unsafe=True)
                timeout = aiohttp.ClientTimeout(total=15, connect=8)

                async with aiohttp.ClientSession(cookie_jar=jar, connector=connector) as sess:
                    # delay ساده اما موثر
                    await asyncio.sleep(random.uniform(3, 7))

                    async with sess.get(
                        f'https://t.me/{self.channel}/{post}?embed=1&mode=tme',
                        headers={
                            'User-Agent': ua,
                            'Referer': referer,
                            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                            'Accept-Language': 'en-US,en;q=0.9,fa;q=0.8',
                            'Sec-Fetch-Site': 'same-origin',
                            'Sec-Fetch-Mode': 'navigate',
                        },
                        timeout=timeout
                    ) as resp_embed:

                        if 'stel_ssid' not in jar.filter_cookies(resp_embed.url):
                            self.cookie_err += 1
                            break

                        html = await resp_embed.text()
                        token_match = search(r'data-view="([^"]+)"', html)

                        if not token_match:
                            self.token_err += 1
                            break

                        token = token_match.group(1)

                        await asyncio.sleep(random.uniform(1, 3))

                        async with sess.post(
                            f'https://t.me/v/?views={token}',
                            headers={
                                'User-Agent': ua,
                                'Referer': f'{referer}?embed=1&mode=tme',
                                'X-Requested-With': 'XMLHttpRequest',
                                'Origin': 'https://t.me',
                                'Sec-Fetch-Site': 'same-origin',
                                'Sec-Fetch-Mode': 'cors',
                            },
                            timeout=timeout
                        ) as resp_view:

                            text = await resp_view.text()
                            self.completed += 1

                            if resp_view.status == 200 and text.strip() == "true":
                                self.success += 1
                            else:
                                self.failed += 1

                            self.progress()
                            return

            except Exception as e:
                if attempt == max_retries - 1:
                    self.proxy_err += 1
                    self.completed += 1
                    self.progress()
                await asyncio.sleep(1.5 * (attempt + 1))
            finally:
                if 'sess' in locals():
                    await sess.close()

    async def start(self):
        print(f"\n شروع {self.total_views:,} ویو برای @{self.channel} – پست‌ها: {self.posts}")
        print(f" پروکسی فعال: {len(self.proxy_list):,}\n")

        tasks = []
        for post in self.posts:
            for _ in range(self.views_per_post):
                tasks.append(asyncio.create_task(self.view_post(post)))
                await asyncio.sleep(random.uniform(0.1, 0.4))

        await asyncio.gather(*tasks, return_exceptions=True)

        elapsed = time.time() - self.start_time
        print("\n\n" + "═"*65)
        print(f"  نتایج نهایی ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
        print(f"  زمان کل     : {elapsed:.1f} ثانیه")
        print(f"  سرعت میانگین: {self.completed/elapsed:.1f} ویو/ثانیه")
        print(f"  موفق        : {self.success}")
        print(f"  ناموفق      : {self.failed}")
        print(f"  پروکسی خطا  : {self.proxy_err}")
        print(f"  کوکی خطا    : {self.cookie_err}")
        print(f"  توکن خطا    : {self.token_err}")
        print("═"*65)

def parse_posts(inp: str):
    posts = set()
    for part in inp.split(','):
        part = part.strip()
        if '-' in part:
            s, e = map(int, part.split('-'))
            posts.update(range(s, e + 1))
        else:
            posts.add(int(part))
    return sorted(posts)

async def main():
    print("\n" + "═"*70)
    print(" TELEGRAM VIEWS BOOSTER 2026 – STABLE EDITION ".center(70))
    print("═"*70)

    sources = read_config()
    proxies = await scrape_proxies(sources)

    if len(proxies) < 50:
        print("\n [!!!] پروکسی خیلی کم است – حداقل ۲۰۰–۵۰۰ تا نیاز است")
        return

    channel = input("\nنام کانال (بدون @): ").strip()
    posts_str = input("شماره پست‌ها (مثال: 15 یا 20-35 یا 5,8,12-18): ").strip()
    posts = parse_posts(posts_str)
    count = int(input("تعداد ویو برای هر پست: ").strip())

    print("\n" + "═"*70)
    bot = TelegramViews(channel, posts, count, proxies)
    await bot.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n توقف توسط کاربر")
    except Exception as e:
        print(f"\n خطا: {e}")
