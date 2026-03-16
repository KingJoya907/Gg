#!/usr/bin/env python3
# Telegram View Bot - Ultra Fast Version
# BYPASS ALL LIMITS - MAX SPEED

import os
import sys
import re
import socket
import threading
from threading import Thread
from time import sleep, time
from queue import Queue, Empty
from configparser import ConfigParser
import requests

# ========== INSTALL DEPENDENCIES ==========
try:
    import socks
except:
    os.system('pip install pysocks')
    import socks

# ========== CONFIGURATION ==========
THREADS = 5000           # حداکثر نخ‌ها (بر اساس قدرت سیستم)
TIMEOUT = 3              # تایم‌اوت پایین برای سرعت بیشتر
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
PROXY_CHECK_TIMEOUT = 2  # تایم‌اوت چک کردن پروکسی

# Proxy types
PROXY_TYPES = ['http', 'socks4', 'socks5']

# ========== REGEX PATTERNS ==========
IP_PATTERN = r'(?:[0-9]{1,3}\.){3}[0-9]{1,3}'
PORT_PATTERN = r'(?:[0-9]{1,5})'
PROXY_REGEX = re.compile(f'({IP_PATTERN}):({PORT_PATTERN})')

# ========== GLOBALS ==========
proxy_queues = {
    'http': Queue(maxsize=10000),
    'socks4': Queue(maxsize=10000),
    'socks5': Queue(maxsize=10000)
}

stats = {
    'total': 0,
    'working': 0,
    'failed': 0,
    'token_errors': 0,
    'views_sent': 0,
    'start_time': time()
}

channel = ''
post = 0
running = True
view_token = None
session_cookies = None

# ========== LOAD CONFIG ==========
cfg = ConfigParser(interpolation=None)
if not cfg.read("config.ini"):
    print("[!] ERROR: config.ini not found!")
    print("[+] Creating default config.ini...")
    
    with open("config.ini", "w") as f:
        f.write("""[HTTP]
Sources = https://raw.githubusercontent.com/TheSpeedX/PROXY-LIST/master/http.txt
          https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt
          https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt

[SOCKS4]
Sources = https://raw.githubusercontent.com/TheSpeedX/PROXY-LIST/master/socks4.txt
          https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks4.txt
          https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt

[SOCKS5]
Sources = https://raw.githubusercontent.com/TheSpeedX/PROXY-LIST/master/socks5.txt
          https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt
          https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt
""")
    cfg.read("config.ini")

# ========== UTILITY FUNCTIONS ==========
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_status():
    """نمایش آمار لحظه‌ای"""
    elapsed = int(time() - stats['start_time'])
    speed = stats['views_sent'] / (elapsed if elapsed > 0 else 1)
    
    clear_screen()
    print(f"""
╔══════════════════════════════════════════════════════════╗
║                    تلگرام ویو زن حرفه‌ای                    ║
╠══════════════════════════════════════════════════════════╣
║  Channel: {channel:<30} Post: {post:<5}              ║
╠══════════════════════════════════════════════════════════╣
║  ویوهای ارسالی: {stats['views_sent']:<15} سرعت: {speed:.1f}/sec     ║
║  پروکسی فعال: {stats['working']:<15} پروکسی کل: {stats['total']:<10} ║
║  خطاها: {stats['failed']:<17} خطای توکن: {stats['token_errors']:<10} ║
║  زمان فعال: {elapsed//3600:02d}:{(elapsed%3600)//60:02d}:{elapsed%60:02d}                         ║
╚══════════════════════════════════════════════════════════╝
    """, flush=True)

# ========== PROXY SCRAPER ==========
def scrape_proxies(proxy_type):
    """استخراج سریع پروکسی از منابع"""
    sources = cfg.get(proxy_type.upper(), "Sources", fallback="").splitlines()
    queue = proxy_queues[proxy_type]
    
    for source in sources:
        source = source.strip()
        if not source:
            continue
            
        try:
            # استفاده از سشن مجزا برای هر منبع
            session = requests.Session()
            response = session.get(
                source, 
                timeout=TIMEOUT,
                headers={'User-Agent': USER_AGENT}
            )
            
            if response.status_code == 200:
                # استخراج مستقیم با regex
                matches = PROXY_REGEX.findall(response.text)
                for ip, port in matches:
                    if queue.qsize() < 9000:  # جلوگیری از پر شدن بیش از حد
                        proxy = f"{ip}:{port}"
                        queue.put(proxy)
                        stats['total'] += 1
                        
        except Exception as e:
            continue
            
        sleep(0.1)  # کمی مکث بین درخواست‌ها

def start_scrapers():
    """راه‌اندازی همزمان همه اسکرپرها"""
    threads = []
    for pt in PROXY_TYPES:
        for i in range(3):  # ۳ نخ برای هر نوع پروکسی
            t = Thread(target=scrape_proxies, args=(pt,), daemon=True)
            t.start()
            threads.append(t)
    return threads

# ========== PROXY CHECKER ==========
def check_proxy_quick(proxy, proxy_type):
    """چک کردن سریع پروکسی با اتصال به تلگرام"""
    try:
        if proxy_type == 'http':
            proxies = {'http': f'http://{proxy}', 'https': f'http://{proxy}'}
        else:
            proxies = {'http': f'{proxy_type}://{proxy}', 'https': f'{proxy_type}://{proxy}'}
        
        # درخواست سریع به تلگرام
        start = time()
        r = requests.get(
            'https://t.me',
            proxies=proxies,
            timeout=PROXY_CHECK_TIMEOUT,
            headers={'User-Agent': USER_AGENT}
        )
        
        if r.status_code == 200 and (time() - start) < 3:
            stats['working'] += 1
            return True
            
    except:
        stats['failed'] += 1
        
    return False

# ========== GET TOKEN ==========
def get_token_fast(proxy, proxy_type):
    """گرفتن توکن با سرعت بالا"""
    try:
        session = requests.Session()
        
        if proxy_type == 'http':
            session.proxies = {'http': f'http://{proxy}', 'https': f'http://{proxy}'}
        else:
            session.proxies = {'http': f'{proxy_type}://{proxy}', 'https': f'{proxy_type}://{proxy}'}
        
        # درخواست مستقیم بدون سربار اضافی
        response = session.get(
            f'https://t.me/{channel}/{post}',
            params={'embed': '1', 'mode': 'tme'},
            headers={
                'User-Agent': USER_AGENT,
                'Referer': f'https://t.me/{channel}/{post}'
            },
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            # استخراج سریع توکن
            token_match = re.search(r'data-view="(\d+)"', response.text)
            if token_match:
                return token_match.group(1), session
                
    except:
        pass
        
    return None, None

# ========== SEND VIEW ==========
def send_view_fast(token, session):
    """ارسال ویو با حداکثر سرعت"""
    try:
        # کوکی‌های ضروری
        cookies = {
            'stel_dt': '-240',
            'stel_web_auth': 'https%3A%2F%2Fweb.telegram.org%2Fz%2F'
        }
        
        # اضافه کردن کوکی‌های سشن
        if session.cookies:
            cookies.update(session.cookies.get_dict())
        
        response = session.get(
            'https://t.me/v/',
            params={'views': token},
            cookies=cookies,
            headers={
                'User-Agent': USER_AGENT,
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': f'https://t.me/{channel}/{post}?embed=1&mode=tme'
            },
            timeout=TIMEOUT
        )
        
        if response.status_code == 200 and response.text.strip() == 'true':
            stats['views_sent'] += 1
            return True
            
    except:
        pass
        
    return False

# ========== WORKER ==========
def worker(proxy_type):
    """نخ اصلی کارگر"""
    queue = proxy_queues[proxy_type]
    
    while running:
        try:
            # گرفتن پروکسی از صف
            proxy = queue.get(timeout=1)
            
            # چک سریع پروکسی
            if not check_proxy_quick(proxy, proxy_type):
                queue.task_done()
                continue
            
            # گرفتن توکن
            token, session = get_token_fast(proxy, proxy_type)
            
            if token and session:
                # ارسال ویو
                if send_view_fast(token, session):
                    stats['views_sent'] += 1
                    
                # تلاش مجدد با همین پروکسی
                for _ in range(5):  # ۵ بار تلاش با یک پروکسی
                    token2, session2 = get_token_fast(proxy, proxy_type)
                    if token2 and session2:
                        if send_view_fast(token2, session2):
                            stats['views_sent'] += 1
                    sleep(0.05)
            else:
                stats['token_errors'] += 1
                
            queue.task_done()
            
        except Empty:
            continue
        except Exception as e:
            continue

# ========== VIEW MONITOR ==========
def monitor_views():
    """مانیتورینگ ویو واقعی"""
    global view_token, session_cookies
    
    while running:
        try:
            # گرفتن صفحه پست
            r = requests.get(
                f'https://t.me/{channel}/{post}',
                params={'embed': '1', 'mode': 'tme'},
                headers={'User-Agent': USER_AGENT},
                timeout=TIMEOUT
            )
            
            if r.status_code == 200:
                # استخراج تعداد ویو
                views_match = re.search(r'<span class="tgme_widget_message_views">([^<]+)', r.text)
                if views_match:
                    views_text = views_match.group(1)
                    
                    # تبدیل به عدد
                    if 'K' in views_text:
                        real_views = int(float(views_text.replace('K', '')) * 1000)
                    elif 'M' in views_text:
                        real_views = int(float(views_text.replace('M', '')) * 1000000)
                    else:
                        real_views = int(views_text.replace(',', ''))
                    
                    # نمایش وضعیت
                    print_status()
                    
        except:
            pass
            
        sleep(2)

# ========== MAIN ==========
def main():
    global channel, post, running
    
    clear_screen()
    
    # دریافت لینک
    url = input("[?] لینک پست تلگرام را وارد کنید: ").strip()
    
    try:
        if 't.me/' in url:
            parts = url.split('t.me/')[1].split('/')
            channel = parts[0]
            post = int(parts[1])
        else:
            channel, post = url.split('/')
            post = int(post)
    except:
        print("[!] لینک نامعتبر است!")
        return
    
    print(f"[+] هدف: {channel} - پست {post}")
    print("[+] راه‌اندازی سیستم...")
    
    # راه‌اندازی اسکرپرها
    scraper_threads = start_scrapers()
    
    # صبر برای جمع‌آوری پروکسی
    print("[+] در حال جمع‌آوری پروکسی...")
    sleep(3)
    
    # راه‌اندازی کارگرها
    worker_count = min(THREADS, 2000)  # محدودیت برای پایداری
    print(f"[+] راه‌اندازی {worker_count} نخ کاری...")
    
    for i in range(worker_count):
        # توزیع بین انواع پروکسی
        pt = PROXY_TYPES[i % 3]
        t = Thread(target=worker, args=(pt,), daemon=True)
        t.start()
    
    # راه‌اندازی مانیتور
    monitor = Thread(target=monitor_views, daemon=True)
    monitor.start()
    
    print("[+] سیستم فعال شد! در حال ارسال ویو...")
    print("[+] برای توقف Ctrl+C بزنید")
    
    try:
        while running:
            sleep(1)
            # نمایش آمار هر ۵ ثانیه
            if int(time()) % 5 == 0:
                print_status()
    except KeyboardInterrupt:
        print("\n[!] توقف سیستم...")
        running = False

if __name__ == "__main__":
    # افزایش محدودیت نخ‌ها
    threading.stack_size(65536)
    
    # غیرفعال کردن warningها
    requests.packages.urllib3.disable_warnings()
    
    main()
