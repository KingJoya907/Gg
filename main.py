#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Telegram View Bot 2026 - Termux Optimized
Anti-block, High Performance, Socks5 Support
"""

import os
import sys
import re
import time
import json
import random
import threading
import socket
from datetime import datetime
from collections import deque
from urllib.parse import urlparse

# نصب خودکار پیش‌نیازها در ترموکس
def install_dependencies():
    required = {
        'requests': 'requests',
        'socks': 'pysocks',
        'fake_headers': 'fake-headers',
        'cloudscraper': 'cloudscraper'
    }
    
    for module, package in required.items():
        try:
            __import__(module)
        except ImportError:
            os.system(f'pip install {package} --quiet')
            print(f"✅ {package} نصب شد")

install_dependencies()

import requests
import socks
import cloudscraper
from fake_headers import Headers

# ==================== تنظیمات اصلی ====================
class Config:
    # تنظیمات عمومی
    MAX_THREADS = 300  # برای ترموکس کمتر بذارید
    REQUEST_TIMEOUT = 10
    RETRY_COUNT = 2
    REQUEST_DELAY = 0.3
    
    # تنظیمات پروکسی
    PROXY_TIMEOUT = 5
    PROXY_TEST_URL = 'http://httpbin.org/ip'
    MAX_PROXY_AGE = 300  # ثانیه
    
    # User Agents جدید 2026
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1'
    ]
    
    # API‌های جدید پروکسی 2026
    PROXY_SOURCES = {
        'http': [
            'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=5000&country=all',
            'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
            'https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt',
            'https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt'
        ],
        'socks4': [
            'https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks4&timeout=5000&country=all',
            'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt',
            'https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt'
        ],
        'socks5': [
            'https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks5&timeout=5000&country=all',
            'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt',
            'https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt',
            'https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt'
        ]
    }

# ==================== کلاس مدیریت پروکسی ====================
class ProxyManager:
    def __init__(self):
        self.proxies = {
            'http': deque(maxlen=1000),
            'socks4': deque(maxlen=1000),
            'socks5': deque(maxlen=1000)
        }
        self.bad_proxies = set()
        self.lock = threading.Lock()
        self.last_update = 0
        
    def fetch_proxies(self, proxy_type):
        """گرفتن پروکسی از منابع مختلف"""
        proxies = []
        sources = Config.PROXY_SOURCES.get(proxy_type, [])
        
        for url in sources:
            try:
                scraper = cloudscraper.create_scraper()
                response = scraper.get(url, timeout=Config.PROXY_TIMEOUT)
                
                if response.status_code == 200:
                    # استخراج پروکسی‌ها با regex
                    found = re.findall(r'\d+\.\d+\.\d+\.\d+:\d+', response.text)
                    
                    # تست سریع پروکسی‌ها
                    for proxy in found[:50]:  # محدودیت برای سرعت
                        if self.test_proxy(proxy, proxy_type):
                            proxies.append(proxy)
                            
                    print(f"📡 {len(found)} پروکسی {proxy_type} از {url} دریافت شد")
                    
            except Exception as e:
                continue
                
            time.sleep(1)
            
        return list(set(proxies))  # حذف تکراری‌ها
        
    def test_proxy(self, proxy, proxy_type):
        """تست سلامت پروکسی"""
        try:
            if proxy_type == 'http':
                test_proxies = {
                    'http': f'http://{proxy}',
                    'https': f'http://{proxy}'
                }
            else:
                test_proxies = {
                    'http': f'{proxy_type}://{proxy}',
                    'https': f'{proxy_type}://{proxy}'
                }
                
            response = requests.get(
                'http://httpbin.org/ip',
                proxies=test_proxies,
                timeout=Config.PROXY_TIMEOUT
            )
            
            return response.status_code == 200
            
        except:
            return False
            
    def update_proxies(self):
        """به‌روزرسانی لیست پروکسی‌ها"""
        if time.time() - self.last_update < 60:  # آپدیت هر ۱ دقیقه
            return
            
        print("\n🔄 در حال دریافت پروکسی‌های جدید...")
        
        threads = []
        for proxy_type in ['http', 'socks4', 'socks5']:
            thread = threading.Thread(
                target=self._update_type,
                args=(proxy_type,)
            )
            threads.append(thread)
            thread.start()
            time.sleep(0.5)
            
        for thread in threads:
            thread.join()
            
        self.last_update = time.time()
        
        # نمایش آمار
        total = sum(len(p) for p in self.proxies.values())
        print(f"\n✅ {total} پروکسی فعال آماده است")
        
    def _update_type(self, proxy_type):
        """به‌روزرسانی یک نوع پروکسی خاص"""
        new_proxies = self.fetch_proxies(proxy_type)
        
        with self.lock:
            for proxy in new_proxies:
                if proxy not in self.bad_proxies:
                    self.proxies[proxy_type].append(proxy)
                    
    def get_proxy(self, proxy_type='http'):
        """گرفتن یک پروکسی از لیست"""
        with self.lock:
            if self.proxies[proxy_type]:
                proxy = self.proxies[proxy_type].popleft()
                self.proxies[proxy_type].append(proxy)  # برگردوندن به انتهای صف
                return proxy
        return None
        
    def mark_bad(self, proxy, proxy_type):
        """علامت زدن پروکسی خراب"""
        with self.lock:
            self.bad_proxies.add(proxy)
            # حذف از لیست اصلی
            if proxy in self.proxies[proxy_type]:
                self.proxies[proxy_type].remove(proxy)

# ==================== کلاس اصلی ربات ====================
class TelegramViewBot:
    def __init__(self):
        self.proxy_manager = ProxyManager()
        self.stats = {
            'sent': 0,
            'failed': 0,
            'total_views': 0,
            'start_time': time.time()
        }
        self.running = True
        self.channel = ''
        self.post = ''
        self.lock = threading.Lock()
        
        # ساختار ذخیره‌سازی
        os.makedirs('logs', exist_ok=True)
        
    def log(self, msg, level='info'):
        """ثبت لاگ با زمان"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {msg}")
        
    def get_token(self, proxy, proxy_type):
        """دریافت توکن ویو با روش جدید 2026"""
        headers = {
            'User-Agent': random.choice(Config.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        try:
            if proxy_type == 'http':
                proxies = {
                    'http': f'http://{proxy}',
                    'https': f'http://{proxy}'
                }
            else:
                proxies = {
                    'http': f'{proxy_type}://{proxy}',
                    'https': f'{proxy_type}://{proxy}'
                }
                
            session = requests.Session()
            
            # مرحله ۱: دریافت صفحه اصلی
            url = f'https://t.me/{self.channel}/{self.post}'
            params = {
                'embed': '1',
                'mode': 'tme',
                'v': str(int(time.time()))  # کش شکن
            }
            
            response = session.get(
                url,
                params=params,
                headers=headers,
                proxies=proxies,
                timeout=Config.REQUEST_TIMEOUT
            )
            
            # استخراج توکن با روش‌های مختلف
            token = None
            
            # روش ۱: data-view
            match = re.search(r'data-view="([^"]+)"', response.text)
            if match:
                token = match.group(1)
                
            # روش ۲: data-view-id
            if not token:
                match = re.search(r'data-view-id="([^"]+)"', response.text)
                if match:
                    token = match.group(1)
                    
            # روش ۳: views counter
            if not token:
                match = re.search(r'data-counter="([^"]+)"', response.text)
                if match:
                    token = match.group(1)
                    
            if token:
                return token, session, proxies
                
        except Exception as e:
            pass
            
        return None, None, None
        
    def send_view(self, token, session, proxies):
        """ارسال ویو با روش جدید"""
        headers = {
            'User-Agent': random.choice(Config.USER_AGENTS),
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'X-Requested-With': 'XMLHttpRequest',
            'Connection': 'keep-alive',
            'Referer': f'https://t.me/{self.channel}/{self.post}?embed=1&mode=tme',
            'Origin': 'https://t.me'
        }
        
        try:
            response = session.get(
                'https://t.me/v/',
                params={'views': token},
                headers=headers,
                proxies=proxies,
                timeout=Config.REQUEST_TIMEOUT
            )
            
            # بررسی پاسخ
            if response.status_code == 200:
                if response.text.strip() in ['true', 'ok', '1']:
                    return True
                    
        except:
            pass
            
        return False
        
    def worker(self, proxy_type='http'):
        """کارگر اصلی برای ارسال ویو"""
        while self.running:
            proxy = self.proxy_manager.get_proxy(proxy_type)
            
            if not proxy:
                time.sleep(2)
                continue
                
            # دریافت توکن
            token, session, proxies = self.get_token(proxy, proxy_type)
            
            if not token:
                with self.lock:
                    self.stats['failed'] += 1
                    self.proxy_manager.mark_bad(proxy, proxy_type)
                continue
                
            # ارسال ویو
            success = self.send_view(token, session, proxies)
            
            with self.lock:
                if success:
                    self.stats['sent'] += 1
                else:
                    self.stats['failed'] += 1
                    self.proxy_manager.mark_bad(proxy, proxy_type)
                    
            time.sleep(Config.REQUEST_DELAY)
            
    def monitor_views(self):
        """نظارت بر تعداد بازدیدها"""
        scraper = cloudscraper.create_scraper()
        
        while self.running:
            try:
                url = f'https://t.me/{self.channel}/{self.post}'
                headers = {'User-Agent': random.choice(Config.USER_AGENTS)}
                
                response = scraper.get(url, headers=headers, timeout=10)
                
                # استخراج تعداد بازدید
                patterns = [
                    r'<span class="tgme_widget_message_views">([^<]+)',
                    r'data-view-counter="([^"]+)"',
                    r'"views":(\d+)'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, response.text)
                    if match:
                        views = match.group(1).strip()
                        # پاک کردن کاما و کاراکترهای اضافی
                        views = re.sub(r'[^\d]', '', views)
                        if views:
                            self.stats['total_views'] = int(views)
                            break
                            
            except:
                pass
                
            time.sleep(5)
            
    def show_status(self):
        """نمایش وضعیت"""
        while self.running:
            elapsed = int(time.time() - self.stats['start_time'])
            hours = elapsed // 3600
            minutes = (elapsed % 3600) // 60
            seconds = elapsed % 60
            
            # محاسبه سرعت
            if elapsed > 0:
                speed = self.stats['sent'] / elapsed
            else:
                speed = 0
                
            # پاک کردن صفحه و نمایش آمار
            os.system('clear')
            
            print("="*60)
            print("🤖 Telegram View Bot 2026 - Termux Edition")
            print("="*60)
            print(f"📌 کانال: {self.channel}")
            print(f"📌 پست: {self.post}")
            print("-"*60)
            print(f"✅ ویوهای ارسال شده: {self.stats['sent']}")
            print(f"❌ ویوهای ناموفق: {self.stats['failed']}")
            print(f"👁️ بازدید فعلی: {self.stats['total_views']:,}")
            print(f"⚡ سرعت: {speed:.1f} ویو/ثانیه")
            print(f"⏱️ زمان اجرا: {hours:02d}:{minutes:02d}:{seconds:02d}")
            print("-"*60)
            print("🔄 پروکسی‌های فعال:")
            for ptype in ['http', 'socks4', 'socks5']:
                count = len(self.proxy_manager.proxies[ptype])
                print(f"   {ptype}: {count}")
            print("="*60)
            print("🔥 Ctrl+C برای توقف")
            
            time.sleep(1)
            
    def run(self):
        """اجرای اصلی"""
        os.system('clear')
        
        print("="*60)
        print("Telegram View Bot 2026 - Termux Version")
        print("="*60)
        
        # دریافت لینک
        url = input("\n📎 لینک پست تلگرام: ").strip()
        
        try:
            if 't.me/' in url:
                parts = url.split('t.me/')[-1].split('/')
                self.channel = parts[0]
                self.post = parts[1]
            else:
                self.channel, self.post = url.split('/')
        except:
            print("❌ لینک نامعتبر!")
            return
            
        print(f"\n✅ کانال: {self.channel}")
        print(f"✅ پست: {self.post}")
        
        # آپدیت اولیه پروکسی‌ها
        print("\n🔄 دریافت پروکسی‌های اولیه...")
        self.proxy_manager.update_proxies()
        
        # شروع threadها
        threads = []
        
        # Thread پروکسی آپدیت
        update_thread = threading.Thread(target=self._proxy_updater, daemon=True)
        update_thread.start()
        threads.append(update_thread)
        
        # Threadهای کاری
        for i in range(Config.MAX_THREADS):
            proxy_type = random.choice(['http', 'socks4', 'socks5'])
            worker = threading.Thread(
                target=self.worker,
                args=(proxy_type,),
                daemon=True
            )
            worker.start()
            threads.append(worker)
            time.sleep(0.01)
            
        # Thread مانیتورینگ
        monitor = threading.Thread(target=self.monitor_views, daemon=True)
        monitor.start()
        threads.append(monitor)
        
        # Thread نمایش وضعیت
        status = threading.Thread(target=self.show_status, daemon=True)
        status.start()
        threads.append(status)
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n🛑 توقف...")
            self.running = False
            time.sleep(2)
            
    def _proxy_updater(self):
        """به‌روزرسانی دوره‌ای پروکسی‌ها"""
        while self.running:
            time.sleep(120)  # آپدیت هر ۲ دقیقه
            self.proxy_manager.update_proxies()

# ==================== اجرای اصلی ====================
if __name__ == "__main__":
    bot = TelegramViewBot()
    bot.run()
