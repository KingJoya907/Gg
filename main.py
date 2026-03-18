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

user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"
REGEX = compile(
    r"(?:^|\D)?(("
    + r"(?:[1-9]|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
    + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
    + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
    + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
    + r"):" + r"(?:\d|[1-9]\d{1,3}|[1-5]\d{4}|6[0-4]\d{3}"
    + r"|65[0-4]\d{2}|655[0-2]\d|6553[0-5])"
    + r")(?:\D|$)"
)

# ==================== خواندن config.ini ====================
def read_config():
    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8')
    
    sources = []
    if 'SOCKS5' in config:
        sources = [s.strip() for s in config['SOCKS5']['Sources'].splitlines() if s.strip()]
        print(f" [✓] Found {len(sources)} proxy sources in config.ini")
    else:
        print(" [❌] SOCKS5 section not found in config.ini!")
        print(" Creating default config.ini...")
        with open('config.ini', 'w', encoding='utf-8') as f:
            f.write("""[SOCKS5]
Sources = 
    https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt
    https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks5.txt
    https://raw.githubusercontent.com/elliottophellia/yakumo/master/results/socks5/global/socks5_checked.txt
""")
        return read_config()
    
    return sources

# ==================== اسکرپ پروکسی ====================
async def scrape_proxies(sources):
    """اسکرپ پروکسی از منابع config.ini"""
    proxies = []
    print("\n [*] Scraping proxies from sources...")
    
    async with aiohttp.ClientSession() as session:
        for source in sources:
            try:
                print(f" [*] Fetching: {source[:50]}...")
                async with session.get(source, timeout=10) as response:
                    if response.status == 200:
                        html = await response.text()
                        matches = REGEX.finditer(html)
                        found = [m.group(1) for m in matches]
                        proxies.extend(found)
                        print(f" [✓] Found {len(found)} proxies")
                    else:
                        print(f" [✗] HTTP {response.status}")
            except Exception as e:
                print(f" [✗] Error: {str(e)[:30]}")
    
    print(f"\n [✓] Total proxies: {len(proxies)}")
    return proxies

class Telegram:
    def __init__(self, channel: str, posts: list, tasks: int, proxy_list: list) -> None:
        self.tasks = tasks
        self.channel = channel
        self.posts = posts
        self.proxy_list = proxy_list
        self.cookie_error = 0
        self.success_sent = 0
        self.failed_sent = 0
        self.token_error = 0
        self.proxy_error = 0
        self.total_views = tasks * len(posts)
        self.completed = 0
        self.start_time = time.time()
        self.proxy_index = 0

    def show_progress(self):
        percent = (self.completed / self.total_views) * 100
        bar = '█' * int(percent/2) + '░' * (50 - int(percent/2))
        elapsed = time.time() - self.start_time
        rate = self.completed / elapsed if elapsed > 0 else 0
        
        print(f"\r[{bar}] {percent:.1f}% | ✅ {self.success_sent} | ❌ {self.failed_sent} | ⚠️ {self.proxy_error} | 📊 {rate:.1f}/sec", end='', flush=True)

    def get_next_proxy(self):
        """Get next proxy from list (round-robin)"""
        if not self.proxy_list:
            return None
        proxy = self.proxy_list[self.proxy_index % len(self.proxy_list)]
        self.proxy_index += 1
        return proxy

    async def request(self, post: int, retries: int = 2):
        proxy = self.get_next_proxy()
        if not proxy:
            self.proxy_error += 1
            self.completed += 1
            self.show_progress()
            return
            
        connector = ProxyConnector.from_url(f'socks5://{proxy}')
        jar = aiohttp.CookieJar(unsafe=True)
        
        for attempt in range(retries):
            try:
                async with aiohttp.ClientSession(cookie_jar=jar, connector=connector) as session:
                    # Random delay to appear human
                    await asyncio.sleep(random.uniform(0.5, 1.5))
                    
                    async with session.get(
                        f'https://t.me/{self.channel}/{post}?embed=1&mode=tme', 
                        headers={
                            'referer': f'https://t.me/{self.channel}/{post}',
                            'user-agent': user_agent
                        }, timeout=aiohttp.ClientTimeout(total=10)
                    ) as embed_response:
                        
                        if jar.filter_cookies(embed_response.url).get('stel_ssid'):
                            html = await embed_response.text()
                            views_token = search('data-view="([^"]+)"', html)
                            
                            if views_token:
                                await asyncio.sleep(random.uniform(0.3, 0.8))
                                
                                views_response = await session.post(
                                    'https://t.me/v/?views=' + views_token.group(1), 
                                    headers={
                                        'referer': f'https://t.me/{self.channel}/{post}?embed=1&mode=tme',
                                        'user-agent': user_agent, 
                                        'x-requested-with': 'XMLHttpRequest'
                                    }, timeout=aiohttp.ClientTimeout(total=10)
                                )
                                
                                self.completed += 1
                                response_text = await views_response.text()
                                
                                if response_text == "true" and views_response.status == 200:
                                    self.success_sent += 1
                                else:
                                    self.failed_sent += 1
                                
                                self.show_progress()
                                return
                            else:
                                self.token_error += 1
                        else:
                            self.cookie_error += 1
                            
            except Exception as e:
                if attempt + 1 == retries:
                    self.proxy_error += 1
                    self.completed += 1
                    self.show_progress()
                await asyncio.sleep(1)
            finally:
                jar.clear()

    async def run(self):
        print(f"\n🚀 Starting {self.total_views} views on @{self.channel} posts: {self.posts}")
        print(f"🔧 Using {len(self.proxy_list)} proxies from config.ini\n")
        
        # Create tasks for all views
        tasks = []
        for post in self.posts:
            for _ in range(self.tasks):
                tasks.append(asyncio.create_task(self.request(post)))
        
        # Run all tasks
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Final results
        elapsed = time.time() - self.start_time
        print(f"\n\n📊 FINAL RESULTS:")
        print(f"   ⏱️  Time: {elapsed:.1f} seconds")
        print(f"   📈 Avg Rate: {self.completed/elapsed:.1f} views/sec")
        print(f"   ✅ Success: {self.success_sent}")
        print(f"   ❌ Failed: {self.failed_sent}")
        print(f"   ⚠️ Proxy Errors: {self.proxy_error}")
        print(f"   🍪 Cookie Errors: {self.cookie_error}")
        print(f"   🔑 Token Errors: {self.token_error}")

def parse_posts(post_input):
    posts = set()
    ranges = post_input.split(',')
    for r in ranges:
        r = r.strip()
        if '-' in r:
            start, end = map(int, r.split('-'))
            posts.update(range(start, end + 1))
        else:
            posts.add(int(r))
    return sorted(list(posts))

async def main():
    print("\n" + "="*60)
    print("🚀 TELEGRAM AUTO VIEWS - CONFIG.INI EDITION 🚀".center(60))
    print("="*60)
    
    # Read proxies from config.ini
    sources = read_config()
    proxies = await scrape_proxies(sources)
    
    if not proxies:
        print("\n [❌] No proxies found! Exiting...")
        return
    
    print(f"\n [✓] Loaded {len(proxies)} proxies from config.ini")
    
    # Get target info
    channel = input("\nChannel (without @): ").strip()
    post_input = input("Post numbers (e.g., 1-10 or 4,5,6-10): ").strip()
    posts = parse_posts(post_input)
    views = int(input("Number of views per post: ").strip())
    
    print("\n" + "="*60)
    
    # Run the bot
    api = Telegram(channel, posts, views, proxies)
    await api.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
