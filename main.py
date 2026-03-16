import os
import sys
import threading
import re
import time
from queue import Queue
from datetime import datetime
from configparser import ConfigParser
from typing import Optional, Tuple, List, Dict, Any

# نصب خودکار کتابخانه‌ها
def install_dependencies():
    required_packages = ['requests', 'configparser']
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            print(f"در حال نصب {package}...")
            os.system(f'pip install {package}')
            time.sleep(1)

install_dependencies()

import requests
from requests.exceptions import RequestException

# ========== تنظیمات ==========
class Config:
    THREADS = 100  # کاهش تعداد تردها برای پایداری بیشتر
    PROXY_TYPES = ('http', 'socks4', 'socks5')
    TIMEOUT = 15
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    DELAY_BETWEEN_CYCLES = 30  # تاخیر بین سیکل‌ها
    MAX_PROXIES_PER_TYPE = 1000  # محدودیت تعداد پروکسی
    
    # الگوی regex برای تشخیص پروکسی
    PROXY_REGEX = re.compile(
        r"(?:^|\D)?(("
        r"(?:[1-9]|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
        r"\."
        r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
        r"\."
        r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
        r"\."
        r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
        r"):"
        r"(?:\d|[1-9]\d{1,3}|[1-5]\d{4}|6[0-4]\d{3}|65[0-4]\d{2}|655[0-2]\d|6553[0-5])"
        r")(?:\D|$)"
    )

# ========== مدیریت خطا ==========
class Logger:
    def __init__(self):
        self.error_file = 'errors.txt'
        self.log_file = 'views_log.txt'
        self.lock = threading.Lock()
    
    def log_error(self, message: str):
        with self.lock:
            with open(self.error_file, 'a', encoding='utf-8') as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"[{timestamp}] ERROR: {message}\n")
    
    def log_success(self, message: str):
        with self.lock:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"[{timestamp}] SUCCESS: {message}\n")
    
    def log_info(self, message: str):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

logger = Logger()

# ========== مدیریت کانفیگ ==========
class ConfigManager:
    def __init__(self, config_file: str = 'config.ini'):
        self.config_file = config_file
        self.config = None
        self.http_sources = []
        self.socks4_sources = []
        self.socks5_sources = []
        
    def load(self) -> bool:
        """بارگذاری فایل کانفیگ"""
        if not os.path.exists(self.config_file):
            logger.log_error(f"فایل {self.config_file} یافت نشد")
            return False
        
        try:
            self.config = ConfigParser(interpolation=None)
            self.config.read(self.config_file, encoding='utf-8')
            
            # استخراج منابع
            self.http_sources = self._get_sources('HTTP')
            self.socks4_sources = self._get_sources('SOCKS4')
            self.socks5_sources = self._get_sources('SOCKS5')
            
            logger.log_info("✅ فایل کانفیگ با موفقیت بارگذاری شد")
            return True
            
        except Exception as e:
            logger.log_error(f"خطا در خواندن کانفیگ: {e}")
            return False
    
    def _get_sources(self, section: str) -> List[str]:
        """دریافت منابع از یک بخش خاص"""
        try:
            if section in self.config:
                sources = self.config[section].get('Sources', '').splitlines()
                return [s.strip() for s in sources if s.strip()]
        except Exception as e:
            logger.log_error(f"خطا در دریافت منابع {section}: {e}")
        return []

# ========== اسکراپر پروکسی ==========
class ProxyScraper:
    def __init__(self):
        self.proxies = {
            'http': [],
            'socks4': [],
            'socks5': []
        }
        self.lock = threading.Lock()
    
    def scrape(self, sources: List[str], proxy_type: str, timeout: int = Config.TIMEOUT) -> List[str]:
        """اسکرپ پروکسی از منابع"""
        found_proxies = []
        
        for source in sources:
            if not source:
                continue
                
            try:
                response = requests.get(source, timeout=timeout)
                response.raise_for_status()
                
                # پیدا کردن پروکسی‌ها با regex
                matches = Config.PROXY_REGEX.finditer(response.text)
                for match in matches:
                    proxy = match.group(1)
                    if proxy not in found_proxies:
                        found_proxies.append(proxy)
                        
                logger.log_info(f"🔍 {len(found_proxies)} پروکسی {proxy_type} از {source} پیدا شد")
                
            except RequestException as e:
                logger.log_error(f"خطا در دریافت {source}: {e}")
            except Exception as e:
                logger.log_error(f"خطای ناشناخته در اسکرپ {source}: {e}")
        
        # محدود کردن تعداد پروکسی‌ها
        if len(found_proxies) > Config.MAX_PROXIES_PER_TYPE:
            found_proxies = found_proxies[:Config.MAX_PROXIES_PER_TYPE]
            
        return found_proxies
    
    def scrape_all(self, http_sources: List[str], socks4_sources: List[str], socks5_sources: List[str]):
        """اسکرپ همزمان همه پروکسی‌ها"""
        threads = []
        
        for sources, proxy_type in [
            (http_sources, 'http'),
            (socks4_sources, 'socks4'),
            (socks5_sources, 'socks5')
        ]:
            if sources:
                thread = threading.Thread(
                    target=self._scrape_thread,
                    args=(sources, proxy_type)
                )
                thread.start()
                threads.append(thread)
        
        # منتظر ماندن برای اتمام همه تردها
        for thread in threads:
            thread.join()
        
        # گزارش نهایی
        for ptype, proxies in self.proxies.items():
            logger.log_info(f"📊 مجموع پروکسی‌های {ptype}: {len(proxies)}")
    
    def _scrape_thread(self, sources: List[str], proxy_type: str):
        """ترد برای اسکرپ یک نوع پروکسی"""
        proxies = self.scrape(sources, proxy_type)
        with self.lock:
            self.proxies[proxy_type] = proxies

# ========== مدیریت ویو ==========
class ViewManager:
    def __init__(self, channel: str, post: str):
        self.channel = channel
        self.post = post
        self.stats = {
            'total_views': 0,
            'successful_views': 0,
            'proxy_errors': 0,
            'token_errors': 0,
            'other_errors': 0
        }
        self.stats_lock = threading.Lock()
        self.running = True
        self.current_views = "0"
    
    def get_token(self, proxy: str, proxy_type: str, timeout: int = Config.TIMEOUT) -> Optional[Tuple[str, requests.Session]]:
        """دریافت توکن ویو"""
        try:
            session = requests.Session()
            
            url = f'https://t.me/{self.channel}/{self.post}'
            response = session.get(
                url,
                params={'embed': '1', 'mode': 'tme'},
                headers={
                    'referer': url,
                    'user-agent': Config.USER_AGENT
                },
                proxies={
                    'http': f'{proxy_type}://{proxy}',
                    'https': f'{proxy_type}://{proxy}'
                },
                timeout=timeout
            )
            
            # استخراج توکن
            match = re.search('data-view="([^"]+)', response.text)
            if match:
                return match.group(1), session
            
            return None
            
        except RequestException:
            return None
        except Exception as e:
            logger.log_error(f"خطا در دریافت توکن: {e}")
            return None
    
    def send_view(self, token: str, session: requests.Session, proxy: str, proxy_type: str) -> bool:
        """ارسال ویو"""
        try:
            cookies = session.cookies.get_dict()
            
            response = session.get(
                'https://t.me/v/',
                params={'views': token},
                cookies={
                    'stel_dt': '-240',
                    'stel_web_auth': 'https%3A%2F%2Fweb.telegram.org%2Fz%2F',
                    'stel_ssid': cookies.get('stel_ssid', ''),
                    'stel_on': cookies.get('stel_on', '')
                },
                headers={
                    'referer': f'https://t.me/{self.channel}/{self.post}?embed=1&mode=tme',
                    'user-agent': Config.USER_AGENT,
                    'x-requested-with': 'XMLHttpRequest'
                },
                proxies={
                    'http': f'{proxy_type}://{proxy}',
                    'https': f'{proxy_type}://{proxy}'
                },
                timeout=Config.TIMEOUT
            )
            
            return response.status_code == 200 and response.text == 'true'
            
        except RequestException:
            return False
        except Exception as e:
            logger.log_error(f"خطا در ارسال ویو: {e}")
            return False
    
    def process_proxy(self, proxy: str, proxy_type: str):
        """پردازش یک پروکسی"""
        if not self.running:
            return
        
        try:
            # دریافت توکن
            token_result = self.get_token(proxy, proxy_type)
            
            if not token_result:
                with self.stats_lock:
                    self.stats['token_errors'] += 1
                return
            
            token, session = token_result
            
            # ارسال ویو
            success = self.send_view(token, session, proxy, proxy_type)
            
            with self.stats_lock:
                self.stats['total_views'] += 1
                if success:
                    self.stats['successful_views'] += 1
                else:
                    self.stats['proxy_errors'] += 1
                    
        except Exception as e:
            with self.stats_lock:
                self.stats['other_errors'] += 1
            logger.log_error(f"خطا در پردازش پروکسی {proxy}: {e}")
    
    def check_current_views(self):
        """بررسی تعداد ویوهای فعلی"""
        while self.running:
            try:
                url = f'https://t.me/{self.channel}/{self.post}'
                response = requests.get(
                    url,
                    params={'embed': '1', 'mode': 'tme'},
                    headers={
                        'referer': url,
                        'user-agent': Config.USER_AGENT
                    },
                    timeout=Config.TIMEOUT
                )
                
                match = re.search('<span class="tgme_widget_message_views">([^<]+)', response.text)
                if match:
                    self.current_views = match.group(1)
                    logger.log_info(f"👁️ ویوهای فعلی: {self.current_views}")
                    
            except Exception as e:
                logger.log_error(f"خطا در بررسی ویوها: {e}")
            
            time.sleep(10)  # بررسی هر ۱۰ ثانیه
    
    def print_stats(self):
        """نمایش آمار"""
        with self.stats_lock:
            print("\n" + "="*50)
            print(f"📊 آمار فعلی:")
            print(f"   مجموع تلاش‌ها: {self.stats['total_views']}")
            print(f"   ویوهای موفق: {self.stats['successful_views']}")
            print(f"   خطاهای پروکسی: {self.stats['proxy_errors']}")
            print(f"   خطاهای توکن: {self.stats['token_errors']}")
            print(f"   سایر خطاها: {self.stats['other_errors']}")
            print(f"   ویوهای فعلی: {self.current_views}")
            print("="*50 + "\n")

# ========== اجرای اصلی ==========
def main():
    # پاک کردن صفحه
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print("="*60)
    print("       تلگرام ویو زن - نسخه پایدار")
    print("="*60)
    
    # دریافت لینک
    while True:
        url = input("\n📎 لینک پست تلگرام را وارد کنید: ").strip()
        
        # پشتیبانی از فرمت‌های مختلف لینک
        url = url.replace('https://t.me/', '').replace('http://t.me/', '').replace('t.me/', '')
        
        parts = url.split('/')
        if len(parts) >= 2:
            channel, post = parts[0], parts[1]
            break
        else:
            print("❌ فرمت لینک اشتباه است. مثال: https://t.me/ChannelName/123")
    
    # بارگذاری کانفیگ
    config_manager = ConfigManager()
    if not config_manager.load():
        print("❌ خطا در بارگذاری فایل کانفیگ")
        input("برای خروج Enter را بفشارید...")
        return
    
    print(f"\n✅ کانال: {channel}")
    print(f"✅ پست: {post}")
    
    # اسکرپ پروکسی‌ها
    print("\n🔄 در حال اسکرپ پروکسی‌ها...")
    scraper = ProxyScraper()
    scraper.scrape_all(
        config_manager.http_sources,
        config_manager.socks4_sources,
        config_manager.socks5_sources
    )
    
    # ایجاد مدیریت ویو
    view_manager = ViewManager(channel, post)
    
    # شروع ترد بررسی ویوها
    check_thread = threading.Thread(target=view_manager.check_current_views, daemon=True)
    check_thread.start()
    
    # حلقه اصلی
    cycle_count = 0
    
    try:
        while True:
            cycle_count += 1
            print(f"\n🔄 سیکل {cycle_count} شروع شد")
            
            # ایجاد صف برای هر نوع پروکسی
            queues = []
            threads = []
            
            for proxy_type in Config.PROXY_TYPES:
                proxies = scraper.proxies.get(proxy_type, [])
                if proxies:
                    q = Queue()
                    for proxy in proxies:
                        q.put(proxy)
                    queues.append((q, proxy_type))
            
            if not queues:
                print("❌ هیچ پروکسی برای استفاده وجود ندارد")
                break
            
            # ایجاد تردهای worker
            for q, proxy_type in queues:
                for i in range(min(Config.THREADS // len(queues), 25)):  # حداکثر ۲۵ ترد برای هر نوع
                    t = threading.Thread(
                        target=lambda q, pt: process_queue(q, pt, view_manager),
                        args=(q, proxy_type),
                        daemon=True
                    )
                    t.start()
                    threads.append(t)
            
            # منتظر ماندن برای اتمام صف‌ها
            for q, _ in queues:
                q.join()
            
            # نمایش آمار
            view_manager.print_stats()
            
            # تاخیر بین سیکل‌ها
            print(f"⏳ {Config.DELAY_BETWEEN_CYCLES} ثانیه تاخیل تا سیکل بعدی...")
            time.sleep(Config.DELAY_BETWEEN_CYCLES)
            
    except KeyboardInterrupt:
        print("\n\n⛔ توقف برنامه توسط کاربر")
        view_manager.running = False
        view_manager.print_stats()
    
    print("\n👋 برنامه پایان یافت")
    time.sleep(2)

def process_queue(queue: Queue, proxy_type: str, view_manager: ViewManager):
    """پردازش صف پروکسی‌ها"""
    while not queue.empty() and view_manager.running:
        try:
            proxy = queue.get_nowait()
            view_manager.process_proxy(proxy, proxy_type)
        except Queue.Empty:
            break
        except Exception as e:
            logger.log_error(f"خطا در process_queue: {e}")
        finally:
            queue.task_done()

if __name__ == "__main__":
    main()
