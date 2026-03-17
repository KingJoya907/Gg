import aiohttp
import asyncio
from re import search, compile
from argparse import ArgumentParser
from datetime import datetime
from fake_useragent import UserAgent
from aiohttp_socks import ProxyConnector

# Regular expression for matching proxy patterns
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

class Telegram:
    def __init__(self, channel: str, post: int, concurrency: int = 100) -> None:
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
        log(f"Initialized with channel: @{channel}, post: {post}, concurrency: {concurrency}")

    async def print_stats(self):
        while True:
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
            print("="*60)

    async def request(self, proxy: str):
        proxy_url = f"socks5://{proxy}"
        try:
            async with self.semaphore:
                connector = ProxyConnector.from_url(proxy_url)
                jar = aiohttp.CookieJar(unsafe=True)
                async with aiohttp.ClientSession(cookie_jar=jar, connector=connector) as session:
                    user_agent = UserAgent().random
                    headers = {
                        "referer": f"https://t.me/{self.channel}/{self.post}",
                        "user-agent": user_agent,
                    }
                    
                    # Get token
                    async with session.get(
                        f"https://t.me/{self.channel}/{self.post}?embed=1&mode=tme",
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=10),
                    ) as embed_response:

                        if not jar.filter_cookies(embed_response.url).get("stel_ssid"):
                            self.stats['token_errors'] += 1
                            self.stats['failed'] += 1
                            return

                        views_token = search(
                            'data-view="([^"]+)"', await embed_response.text()
                        )

                        if not views_token:
                            self.stats['token_errors'] += 1
                            self.stats['failed'] += 1
                            return

                        # Send view
                        views_response = await session.post(
                            "https://t.me/v/?views=" + views_token.group(1),
                            headers={
                                "referer": f"https://t.me/{self.channel}/{self.post}?embed=1&mode=tme",
                                "user-agent": user_agent,
                                "x-requested-with": "XMLHttpRequest",
                            },
                            timeout=aiohttp.ClientTimeout(total=10),
                        )

                        self.stats['total'] += 1
                        
                        if (
                            await views_response.text() == "true"
                            and views_response.status == 200
                        ):
                            self.stats['success'] += 1
                        else:
                            self.stats['failed'] += 1

        except Exception as e:
            self.stats['proxy_errors'] += 1
            self.stats['failed'] += 1

        finally:
            if 'jar' in locals():
                jar.clear()

    async def run_proxies_continuous(self, lines: list):
        log(f"Starting continuous mode with {len(lines)} SOCKS5 proxies")
        
        # Start stats printer
        asyncio.create_task(self.print_stats())
        
        while True:
            tasks = [
                asyncio.create_task(self.request(proxy))
                for proxy in lines
            ]
            await asyncio.gather(*tasks, return_exceptions=True)

    async def continuous_request(self, proxy: str):
        while True:
            await self.request(proxy)

    async def run_rotated_continuous(self, proxy: str):
        log(f"Starting continuous rotated mode with SOCKS5 proxy {proxy}")
        
        # Start stats printer
        asyncio.create_task(self.print_stats())
        
        tasks = [
            asyncio.create_task(self.continuous_request(proxy))
            for _ in range(self.concurrency * 5)
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

class Auto:
    def __init__(self):
        self.proxies = []
        try:
            with open("auto/socks5.txt", "r") as file:
                self.socks5_sources = file.read().splitlines()
                log(f"Loaded {len(self.socks5_sources)} SOCKS5 proxy sources")
                
        except FileNotFoundError as e:
            log(f"ERROR: auto/socks5.txt not found - {str(e)}")
            exit(0)
        
        log("Starting SOCKS5 proxy scraping from sources...")

    async def scrap(self, source_url):
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"user-agent": UserAgent().random}
                log(f"Scraping SOCKS5 proxies from {source_url}")
                async with session.get(
                    source_url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    html = await response.text()
                    matches = REGEX.finditer(html)
                    found_proxies = [match.group(1) for match in matches]
                    self.proxies.extend(found_proxies)
                    log(f"Found {len(found_proxies)} SOCKS5 proxies from {source_url}")

        except Exception as e:
            log(f"ERROR: Failed to scrape from {source_url} - {str(e)[:100]}")
            with open("error.txt", "a", encoding="utf-8", errors="ignore") as f:
                f.write(f"{source_url} -> {e}\n")

    async def init(self):
        tasks = []
        self.proxies.clear()

        tasks.extend([self.scrap(source_url) for source_url in self.socks5_sources])

        await asyncio.gather(*tasks)
        log(f"Proxy scraping complete. Total SOCKS5 proxies found: {len(self.proxies)}")

async def main():
    parser = ArgumentParser()
    parser.add_argument("-c", "--channel", dest="channel", help="Channel without @ (e.g: MyChannel1234)", type=str, required=True)
    parser.add_argument("-pt", "--post", dest="post", help="Post number (ID) (e.g: 1921)", type=int, required=True)
    parser.add_argument("-m", "--mode", dest="mode", help="Proxy mode (list | auto | rotate)", type=str, required=True)
    parser.add_argument("-p", "--proxy", dest="proxy", help="Proxy file path or proxy address (host:port)", type=str, required=False)
    parser.add_argument("-cc", "--concurrency", dest="concurrency", help="Maximum concurrent requests", type=int, default=200)
    args = parser.parse_args()
    
    log(f"Telegram Views Started - SOCKS5 ONLY - Mode: {args.mode}")
    api = Telegram(args.channel, args.post, args.concurrency)
    
    if args.mode[0] == "l":  # list mode
        with open(args.proxy, "r") as file:
            lines = file.read().splitlines()
        log(f"Loaded {len(lines)} SOCKS5 proxies from file {args.proxy}")
        await api.run_proxies_continuous(lines)

    elif args.mode[0] == "r":  # rotate mode
        log(f"Starting rotated mode with single SOCKS5 proxy: {args.proxy}")
        await api.run_rotated_continuous(args.proxy)

    else:  # auto mode
        auto = Auto()
        await auto.init()
        
        if not auto.proxies:
            log("No SOCKS5 proxies found, exiting...")
            return
            
        log(f"Auto scraping complete. Found {len(auto.proxies)} SOCKS5 proxies")
        await api.run_proxies_continuous(auto.proxies)

if __name__ == "__main__":
    log("Program started - SOCKS5 ONLY EDITION")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log("\nProgram terminated by user")
    except Exception as e:
        log(f"Unhandled exception: {str(e)}")
