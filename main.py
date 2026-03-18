import aiohttp
import asyncio
from re import search, compile
from aiohttp_socks import ProxyConnector
import logging
import time
import sys

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

class Telegram:
    def __init__(self, channel: str, posts: list, tasks: int) -> None:
        self.tasks = tasks
        self.channel = channel
        self.posts = posts
        self.cookie_error = 0
        self.success_sent = 0
        self.failed_sent = 0
        self.token_error = 0
        self.proxy_error = 0
        self.total_views = tasks * len(posts)
        self.completed = 0

    def show_progress(self):
        percent = (self.completed / self.total_views) * 100
        bar = '█' * int(percent/2) + '░' * (50 - int(percent/2))
        print(f"\r[{bar}] {percent:.1f}% | ✅ {self.success_sent} | ❌ {self.failed_sent} | ⚠️ {self.proxy_error}", end='', flush=True)

    async def request(self, proxy: str, proxy_type: str, post: int, retries: int = 3):
        connector = ProxyConnector.from_url(f'socks5://{proxy}')
        jar = aiohttp.CookieJar(unsafe=True)
        for attempt in range(retries):
            try:
                async with aiohttp.ClientSession(cookie_jar=jar, connector=connector) as session:
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
                                views_response = await session.post(
                                    'https://t.me/v/?views=' + views_token.group(1), 
                                    headers={
                                        'referer': f'https://t.me/{self.channel}/{post}?embed=1&mode=tme',
                                        'user-agent': user_agent, 
                                        'x-requested-with': 'XMLHttpRequest'
                                    }, timeout=aiohttp.ClientTimeout(total=10)
                                )
                                self.completed += 1
                                if (await views_response.text() == "true" and views_response.status == 200):
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
                logging.error(f"Attempt {attempt+1}/{retries} failed: {e}")
                if attempt + 1 == retries:
                    self.proxy_error += 1
                    self.completed += 1
                    self.show_progress()
            finally:
                jar.clear()
            await asyncio.sleep(1)

    async def run_rotated_task(self, proxy, proxy_type):
        print(f"\n🚀 Starting {self.total_views} views on @{self.channel} posts: {self.posts}")
        print(f"🔧 Using proxy: {proxy}\n")
        
        tasks = []
        for post in self.posts:
            tasks.extend([asyncio.create_task(self.request(proxy, proxy_type, post)) for _ in range(self.tasks)])
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        print(f"\n\n📊 FINAL RESULTS:")
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
    print("\n" + "="*50)
    print("🚀 TELEGRAM AUTO VIEWS - CLI VERSION")
    print("="*50)
    
    channel = input("Channel (without @): ").strip()
    post_input = input("Post numbers (e.g., 1-10 or 4,5,6-10): ").strip()
    posts = parse_posts(post_input)
    proxy = input("Proxy (user:password@host:port): ").strip()
    views = int(input("Number of views per post: ").strip())
    
    print("\n" + "="*50)
    api = Telegram(channel, posts, views)
    await api.run_rotated_task(proxy, "socks5")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
