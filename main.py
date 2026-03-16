"""
Telegram View Bot - Ultra Optimized Version
سازگار با config.ini شما - بیشترین سرعت ویو
"""

import asyncio
import aiohttp
from aiohttp import ClientTimeout, TCPConnector
import re
from typing import Optional, Tuple, List, Dict, Any, Set
from dataclasses import dataclass, field
from configparser import ConfigParser
import logging
from logging.handlers import RotatingFileHandler
import sys
import os
from colorama import init, Fore, Style
import signal
import random
import time
from collections import deque
import json
import socket
from concurrent.futures import ThreadPoolExecutor
import threading
from urllib.parse import urlparse
import ipaddress

# نصب خودکار کتابخانه‌های مورد نیاز
required_packages = ['aiohttp', 'colorama', 'aiohttp-socks', 'beautifulsoup4']

for package in required_packages:
    try:
        __import__(package.replace('-', '_'))
    except ImportError:
        print(f"در حال نصب {package}...")
        os.system(f'pip install {package} -q')

# تنظیمات رنگ و لاگ
init(autoreset=True)

# تنظیمات لاگینگ
log_format = '%(asctime)s - %(levelname)s - %(message)s'
log_file = 'telegram_viewer.log'

file_handler = RotatingFileHandler(log_file, maxBytes=10_000_000, backupCount=5)
file_handler.setFormatter(logging.Formatter(log_format))

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(
    f'{Fore.GREEN}%(asctime)s{Style.RESET_ALL} - '
    f'{Fore.CYAN}%(levelname)s{Style.RESET_ALL} - %(message)s'
))

logger = logging.getLogger('TelegramViewer')
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)


@dataclass
class Config:
    """کلاس تنظیمات مطابق با config.ini شما"""
    threads: int = 2000
    timeout: int = 8
    max_retries: int = 2
    batch_size: int = 200
    user_agent: str = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    
    # منابع پروکسی از config.ini شما
    http_sources: List[str] = field(default_factory=list)
    socks4_sources: List[str] = field(default_factory=list)
    socks5_sources: List[str] = field(default_factory=list)
    
    # کانال هدف
    channel: str = ''
    post_id: int = 0
    
    # تنظیمات پیشرفته
    proxy_check_timeout: int = 3
    connection_limit: int = 2000
    max_proxies_per_type: int = 5000


class ConfigLoader:
    """بارگذاری تنظیمات از config.ini شما"""
    
    @staticmethod
    def load_from_ini(file_path: str = 'config.ini') -> Config:
        """بارگذاری تنظیمات از فایل INI با ساختار شما"""
        config = Config()
        parser = ConfigParser(interpolation=None)
        
        if not os.path.exists(file_path):
            logger.error(f"❌ فایل {file_path} یافت نشد!")
            logger.info("لطفاً فایل config.ini را در کنار برنامه قرار دهید")
            return config
        
        try:
            parser.read(file_path, encoding='utf-8')
            
            # خواندن منابع HTTP
            if 'HTTP' in parser and 'Sources' in parser['HTTP']:
                sources_text = parser['HTTP']['Sources']
                config.http_sources = [
                    line.strip() for line in sources_text.split('\n') 
                    if line.strip() and not line.strip().startswith(';')
                ]
                logger.info(f"✅ {len(config.http_sources)} منبع HTTP بارگذاری شد")
            
            # خواندن منابع SOCKS4
            if 'SOCKS4' in parser and 'Sources' in parser['SOCKS4']:
                sources_text = parser['SOCKS4']['Sources']
                config.socks4_sources = [
                    line.strip() for line in sources_text.split('\n') 
                    if line.strip() and not line.strip().startswith(';')
                ]
                logger.info(f"✅ {len(config.socks4_sources)} منبع SOCKS4 بارگذاری شد")
            
            # خواندن منابع SOCKS5
            if 'SOCKS5' in parser and 'Sources' in parser['SOCKS5']:
                sources_text = parser['SOCKS5']['Sources']
                config.socks5_sources = [
                    line.strip() for line in sources_text.split('\n') 
                    if line.strip() and not line.strip().startswith(';')
                ]
                logger.info(f"✅ {len(config.socks5_sources)} منبع SOCKS5 بارگذاری شد")
            
            # تنظیمات اضافی می‌توانید اضافه کنید
            if 'SETTINGS' in parser:
                settings = parser['SETTINGS']
                config.threads = int(settings.get('threads', '2000'))
                config.timeout = int(settings.get('timeout', '8'))
                config.max_proxies_per_type = int(settings.get('max_proxies_per_type', '5000'))
            
            total_sources = len(config.http_sources) + len(config.socks4_sources) + len(config.socks5_sources)
            logger.info(f"📊 مجموع منابع پروکسی: {total_sources}")
            
        except Exception as e:
            logger.error(f"خطا در خواندن {file_path}: {e}")
        
        return config


class ProxyCollector:
    """جمع‌آوری پروکسی از منابع config.ini شما"""
    
    IP_PORT_REGEX = re.compile(
        r'(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
        r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)'
        r':([0-9]{1,5})'
    )
    
    def __init__(self, config: Config):
        self.config = config
        self.proxies: Dict[str, List[str]] = {
            'http': [],
            'socks4': [],
            'socks5': []
        }
        self.proxy_queues: Dict[str, asyncio.Queue] = {
            'http': asyncio.Queue(),
            'socks4': asyncio.Queue(),
            'socks5': asyncio.Queue()
        }
        
    async def fetch_source(self, session: aiohttp.ClientSession, url: str, proxy_type: str):
        """دریافت پروکسی از یک منبع"""
        try:
            logger.debug(f"دریافت از {url}")
            async with session.get(url, timeout=ClientTimeout(total=10)) as response:
                if response.status == 200:
                    text = await response.text()
                    
                    # استخراج آی‌پی و پورت
                    lines = text.strip().split('\n')
                    found_proxies = []
                    
                    for line in lines[:1000]:  # محدودیت برای سرعت
                        line = line.strip()
                        # پیدا کردن الگوی آی‌پی:پورت
                        match = self.IP_PORT_REGEX.search(line)
                        if match:
                            # استخراج آی‌پی کامل
                            ip_port = line[:match.end()]
                            if self.validate_ip_port(ip_port):
                                found_proxies.append(ip_port)
                    
                    if found_proxies:
                        self.proxies[proxy_type].extend(found_proxies[:self.config.max_proxies_per_type])
                        logger.debug(f"✅ {len(found_proxies)} پروکسی {proxy_type} از {url}")
                        
        except Exception as e:
            logger.debug(f"خطا در دریافت {url}: {e}")
    
    def validate_ip_port(self, ip_port: str) -> bool:
        """اعتبارسنجی اولیه آی‌پی و پورت"""
        try:
            ip, port = ip_port.split(':')
            port = int(port)
            
            # اعتبارسنجی آی‌پی
            ipaddress.ip_address(ip)
            
            # اعتبارسنجی پورت
            if not (1 <= port <= 65535):
                return False
                
            return True
        except:
            return False
    
    async def collect_all(self):
        """جمع‌آوری پروکسی از همه منابع"""
        connector = TCPConnector(limit=500, ssl=False)
        timeout = ClientTimeout(total=15)
        
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'User-Agent': self.config.user_agent}
        ) as session:
            
            tasks = []
            
            # اضافه کردن تسک‌های HTTP
            for url in self.config.http_sources:
                tasks.append(self.fetch_source(session, url, 'http'))
            
            # اضافه کردن تسک‌های SOCKS4
            for url in self.config.socks4_sources:
                tasks.append(self.fetch_source(session, url, 'socks4'))
            
            # اضافه کردن تسک‌های SOCKS5
            for url in self.config.socks5_sources:
                tasks.append(self.fetch_source(session, url, 'socks5'))
            
            # اجرای همزمان همه تسک‌ها
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            
            # حذف تکراری‌ها
            for proxy_type in self.proxies:
                self.proxies[proxy_type] = list(set(self.proxies[proxy_type]))
            
            # پر کردن صف‌ها
            for proxy_type, proxies in self.proxies.items():
                for proxy in proxies[:self.config.max_proxies_per_type]:
                    await self.proxy_queues[proxy_type].put(proxy)
            
            # گزارش نهایی
            total = sum(len(p) for p in self.proxies.values())
            logger.info(f"{Fore.GREEN}📡 {total:,} پروکسی جمع‌آوری شد:{Style.RESET_ALL}")
            logger.info(f"   HTTP: {len(self.proxies['http']):,}")
            logger.info(f"   SOCKS4: {len(self.proxies['socks4']):,}")
            logger.info(f"   SOCKS5: {len(self.proxies['socks5']):,}")
            
            return total
    
    async def get_proxy(self, proxy_type: str) -> Optional[str]:
        """گرفتن یک پروکسی از صف"""
        try:
            if not self.proxy_queues[proxy_type].empty():
                proxy = await self.proxy_queues[proxy_type].get()
                # برگرداندن به صف برای استفاده مجدد
                await self.proxy_queues[proxy_type].put(proxy)
                return proxy
        except:
            pass
        return None


class TelegramViewer:
    """ویو زن اصلی با حداکثر سرعت"""
    
    def __init__(self, config: Config, collector: ProxyCollector):
        self.config = config
        self.collector = collector
        self.running = True
        self.stats = {
            'total_views': 0,
            'successful_views': 0,
            'proxy_errors': 0,
            'token_errors': 0,
            'start_time': time.time()
        }
        self.session_pool: Dict[str, List[aiohttp.ClientSession]] = {
            'http': [],
            'socks4': [],
            'socks5': []
        }
        self.view_counter = 0
        self.last_views = deque(maxlen=5)
        
        # تنظیم سیگنال‌ها
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """مدیریت خروج"""
        logger.info(f"{Fore.YELLOW}⏹️ در حال توقف...{Style.RESET_ALL}")
        self.running = False
    
    async def create_session_pool(self):
        """ایجاد استخر session برای حداکثر سرعت"""
        connector = TCPConnector(
            limit=0,
            limit_per_host=0,
            ttl_dns_cache=600,
            ssl=False,
            use_dns_cache=True,
            force_close=False,
            enable_cleanup_closed=True
        )
        
        timeout = ClientTimeout(
            total=self.config.timeout,
            connect=3,
            sock_read=self.config.timeout
        )
        
        # ایجاد 500 session برای هر نوع پروکسی
        sessions_per_type = 500
        
        for proxy_type in self.session_pool.keys():
            sessions = []
            for i in range(sessions_per_type):
                session = aiohttp.ClientSession(
                    connector=connector.clone(),
                    timeout=timeout,
                    headers={'User-Agent': self.config.user_agent}
                )
                sessions.append(session)
            self.session_pool[proxy_type] = sessions
        
        logger.info(f"✅ {Fore.GREEN}استخر session با {sessions_per_type*3:,} کانکشن ساخته شد{Style.RESET_ALL}")
    
    async def send_view(self, session: aiohttp.ClientSession, proxy: str, proxy_type: str) -> bool:
        """ارسال ویو با بهینه‌ترین روش"""
        try:
            # گرفتن توکن
            token_url = f'https://t.me/{self.config.channel}/{self.config.post_id}'
            params = {'embed': '1', 'mode': 'tme'}
            headers = {
                'referer': f'https://t.me/{self.config.channel}/{self.config.post_id}',
                'user-agent': self.config.user_agent,
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
            
            proxy_url = f'{proxy_type}://{proxy}'
            
            # دریافت توکن
            async with session.get(
                token_url,
                params=params,
                headers=headers,
                proxy=proxy_url
            ) as response:
                if response.status != 200:
                    self.stats['proxy_errors'] += 1
                    return False
                
                html = await response.text()
                
            # استخراج توکن
            token_match = re.search(r'data-view="(\d+)"', html)
            if not token_match:
                self.stats['token_errors'] += 1
                return False
            
            token = token_match.group(1)
            
            # ارسال ویو
            view_url = 'https://t.me/v/'
            view_params = {'views': token}
            view_headers = {
                'referer': f'https://t.me/{self.config.channel}/{self.config.post_id}?embed=1&mode=tme',
                'user-agent': self.config.user_agent,
                'x-requested-with': 'XMLHttpRequest',
                'accept': 'application/json, text/javascript, */*; q=0.01'
            }
            
            async with session.get(
                view_url,
                params=view_params,
                headers=view_headers,
                proxy=proxy_url
            ) as response:
                if response.status == 200:
                    text = await response.text()
                    if 'true' in text:
                        self.stats['successful_views'] += 1
                        self.stats['total_views'] += 1
                        self.view_counter += 1
                        return True
            
            return False
            
        except asyncio.TimeoutError:
            self.stats['proxy_errors'] += 1
        except aiohttp.ClientError:
            self.stats['proxy_errors'] += 1
        except Exception as e:
            logger.debug(f"خطا: {e}")
        
        return False
    
    async def worker(self, worker_id: int, proxy_type: str):
        """کارگر اصلی"""
        session_index = worker_id % len(self.session_pool[proxy_type])
        session = self.session_pool[proxy_type][session_index]
        
        while self.running:
            try:
                proxy = await self.collector.get_proxy(proxy_type)
                if not proxy:
                    await asyncio.sleep(0.01)
                    continue
                
                await self.send_view(session, proxy, proxy_type)
                
            except Exception as e:
                logger.debug(f"خطا در worker {worker_id}: {e}")
    
    async def monitor_stats(self):
        """مانیتورینگ لحظه‌ای"""
        while self.running:
            elapsed = time.time() - self.stats['start_time']
            vps = self.stats['successful_views'] / elapsed if elapsed > 0 else 0
            
            # محاسبه سرعت لحظه‌ای
            self.last_views.append(self.view_counter)
            if len(self.last_views) > 1:
                instant_vps = (self.last_views[-1] - self.last_views[0]) / len(self.last_views)
            else:
                instant_vps = vps
            
            # پاک کردن صفحه
            os.system('cls' if os.name == 'nt' else 'clear')
            
            # محاسبه درصد موفقیت
            total_requests = self.stats['successful_views'] + self.stats['proxy_errors'] + self.stats['token_errors']
            success_rate = (self.stats['successful_views'] / total_requests * 100) if total_requests > 0 else 0
            
            # نمایش باکس آمار
            print(f"""
{Fore.CYAN}╔════════════════════════════════════════════════════════════════╗
{Fore.CYAN}║         {Fore.YELLOW}🔥 تلگرام ویو زن فوق حرفه‌ای {Fore.CYAN}                        ║
{Fore.CYAN}╠════════════════════════════════════════════════════════════════╣
{Fore.CYAN}║ {Fore.GREEN}کانال:{Style.RESET_ALL} {self.config.channel:<20} {Fore.CYAN}│ {Fore.GREEN}پست:{Style.RESET_ALL} {self.config.post_id}
{Fore.CYAN}╠════════════════════════════════════════════════════════════════╣
{Fore.CYAN}║ {Fore.WHITE}آمار ویو:{Fore.CYAN}                                                    ║
{Fore.CYAN}║ {Fore.GREEN}✅ موفق:{Style.RESET_ALL} {self.stats['successful_views']:>10,} {Fore.CYAN}│ {Fore.YELLOW}🔄 کل:{Style.RESET_ALL} {self.stats['total_views']:>10,}
{Fore.CYAN}║ {Fore.RED}❌ خطا پروکسی:{Style.RESET_ALL} {self.stats['proxy_errors']:>8,} {Fore.CYAN}│ {Fore.RED}⚠️ خطا توکن:{Style.RESET_ALL} {self.stats['token_errors']:>8,}
{Fore.CYAN}╠════════════════════════════════════════════════════════════════╣
{Fore.CYAN}║ {Fore.WHITE}سرعت:{Fore.CYAN}                                                       ║
{Fore.CYAN}║ {Fore.BLUE}📊 متوسط:{Style.RESET_ALL} {vps:>7.1f}/s {Fore.CYAN}│ {Fore.MAGENTA}⚡ لحظه‌ای:{Style.RESET_ALL} {instant_vps:>7.1f}/s
{Fore.CYAN}║ {Fore.CYAN}📈 نرخ موفقیت:{Style.RESET_ALL} {success_rate:>5.1f}% {Fore.CYAN}│ {Fore.WHITE}زمان:{Style.RESET_ALL} {elapsed:>6.0f}s
{Fore.CYAN}╠════════════════════════════════════════════════════════════════╣
{Fore.CYAN}║ {Fore.WHITE}پروکسی‌ها:{Fore.CYAN}                                                   ║
{Fore.CYAN}║ HTTP: {len(self.collector.proxies['http']):>5,}  | SOCKS4: {len(self.collector.proxies['socks4']):>5,}  | SOCKS5: {len(self.collector.proxies['socks5']):>5,}
{Fore.CYAN}╚════════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}""")
            
            await asyncio.sleep(1)
    
    async def run(self):
        """اجرای اصلی"""
        logger.info(f"{Fore.GREEN}🔥 شروع ویو زن فوق حرفه‌ای{Style.RESET_ALL}")
        logger.info(f"🎯 هدف: {self.config.channel}/{self.config.post_id}")
        
        # جمع‌آوری پروکسی
        logger.info(f"{Fore.YELLOW}📡 در حال جمع‌آوری پروکسی از منابع شما...{Style.RESET_ALL}")
        total_proxies = await self.collector.collect_all()
        
        if total_proxies == 0:
            logger.error(f"{Fore.RED}❌ هیچ پروکسی یافت نشد!{Style.RESET_ALL}")
            return
        
        # ایجاد استخر session
        await self.create_session_pool()
        
        # محاسبه تعداد کارگرها برای هر نوع پروکسی
        workers_per_type = self.config.threads // 3
        
        # ایجاد کارگرها
        workers = []
        for proxy_type in ['http', 'socks4', 'socks5']:
            if self.collector.proxies[proxy_type]:
                for i in range(workers_per_type):
                    worker = asyncio.create_task(self.worker(i, proxy_type))
                    workers.append(worker)
        
        logger.info(f"⚙️  {len(workers):,} کارگر فعال شدند")
        
        # مانیتورینگ
        monitor_task = asyncio.create_task(self.monitor_stats())
        
        # منتظر ماندن
        try:
            await asyncio.gather(*workers, return_exceptions=True)
        except:
            pass
        finally:
            monitor_task.cancel()
            await self.cleanup()
    
    async def cleanup(self):
        """پاکسازی"""
        logger.info(f"{Fore.YELLOW}🧹 در حال پاکسازی...{Style.RESET_ALL}")
        
        for sessions in self.session_pool.values():
            for session in sessions:
                await session.close()
        
        elapsed = time.time() - self.stats['start_time']
        logger.info(f"{Fore.GREEN}📊 آمار نهایی:{Style.RESET_ALL}")
        logger.info(f"   ✅ ویوهای موفق: {self.stats['successful_views']:,}")
        logger.info(f"   📊 سرعت متوسط: {self.stats['successful_views']/elapsed:.1f}/s")
        logger.info(f"   ⏱️  زمان: {elapsed:.0f} ثانیه")


async def main():
    """تابع اصلی"""
    print(f"""{Fore.CYAN}
╔══════════════════════════════════════════════════════════════╗
║     {Fore.YELLOW}🔥 تلگرام ویو زن - مخصوص config.ini شما {Fore.CYAN}                ║
║         {Fore.WHITE}با پشتیبانی از منابع GitHub و ProxyScrape{Fore.CYAN}          ║
╚══════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}""")
    
    # بارگذازی تنظیمات از config.ini شما
    config = ConfigLoader.load_from_ini('config.ini')
    
    if not (config.http_sources or config.socks4_sources or config.socks5_sources):
        logger.error(f"{Fore.RED}❌ هیچ منبع پروکسی در config.ini یافت نشد!{Style.RESET_ALL}")
        return
    
    # گرفتن لینک
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("📌 لینک پست تلگرام: ").strip()
    
    # استخراج کانال و پست
    match = re.search(r't\.me/([^/]+)/(\d+)', url)
    if not match:
        logger.error(f"{Fore.RED}❌ لینک نامعتبر!{Style.RESET_ALL}")
        logger.info("فرمت صحیح: https://t.me/username/123")
        return
    
    config.channel, config.post_id = match.groups()
    config.post_id = int(config.post_id)
    
    # اجرا
    collector = ProxyCollector(config)
    viewer = TelegramViewer(config, collector)
    
    try:
        await viewer.run()
    except KeyboardInterrupt:
        logger.info(f"{Fore.YELLOW}⏹️ توقف توسط کاربر{Style.RESET_ALL}")
    except Exception as e:
        logger.error(f"{Fore.RED}❌ خطا: {e}{Style.RESET_ALL}")


if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main())
