"""
TELEGRAM VIEW BOT - ULTIMATE EDITION (FAST VERSION)
"""

import os
import sys
import time
import random
import threading
from datetime import datetime, timedelta
from threading import Thread, active_count
from re import search, compile
from collections import deque

# نصب خودکار کتابخانه‌ها
required_packages = ['requests', 'configparser', 'fake-useragent', 'colorama']

for package in required_packages:
    try:
        __import__(package.replace('-', '_'))
    except ImportError:
        print(f"📦 Installing {package}...")
        os.system(f'pip install {package} -q')

import requests
from time import sleep
from configparser import ConfigParser
from os import system, name
from fake_useragent import UserAgent
from colorama import init, Fore, Style

# تنظیمات اولیه
init(autoreset=True)
system('cls' if name == 'nt' else 'clear')

# ==================== تنظیمات اصلی ====================
THREADS = 1000
PROXIES_TYPES = ('http', 'socks4', 'socks5')
time_out = 5
proxy_update_interval = 300  # 5 دقیقه
max_proxies_per_type = 5000

# ==================== User-Agent هوشمند ====================
try:
    ua = UserAgent()
    def get_ua():
        return ua.random
except:
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]
    def get_ua():
        return random.choice(USER_AGENTS)

# ==================== Regex برای استخراج پروکسی ====================
REGEX = compile(r"(?:^|\D)?(("+ r"(?:[1-9]|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"):" + (r"(?:\d|[1-9]\d{1,3}|[1-5]\d{4}|6[0-4]\d{3}"
                + r"|65[0-4]\d{2}|655[0-2]\d|6553[0-5])")
                + r")(?:\D|$)")

# ==================== فایل خطاها ====================
errors = open('errors.txt', 'a+', encoding='utf-8')

# ==================== بارگذاری config.ini ====================
cfg = ConfigParser(interpolation=None)
cfg.read("config.ini", encoding="utf-8")

try:
    http = cfg["HTTP"]
    socks4 = cfg["SOCKS4"]
    socks5 = cfg["SOCKS5"]
except KeyError:
    print(Fore.RED + "❌ Error | config.ini not found!")
    print(Fore.YELLOW + "📝 Creating default config.ini...")
    
    default_config = """[HTTP]
Sources =
    https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt
    https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt
    https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=5000&country=all

[SOCKS4]
Sources =
    https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt
    https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks4.txt
    https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks4&timeout=5000

[SOCKS5]
Sources =
    https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt
    https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks5.txt
    https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks5&timeout=5000
"""
    with open('config.ini', 'w', encoding='utf-8') as f:
        f.write(default_config)
    
    print(Fore.GREEN + "✅ config.ini created! Please edit it and restart.")
    sleep(5)
    exit()

# ==================== متغیرهای سراسری ====================
http_proxies = []
socks4_proxies = []
socks5_proxies = []
proxy_errors = 0
token_errors = 0
total_views_sent = 0
successful_views = 0
channel = ''
post = 0
real_views = '0'
proxy_scores = {}
view_history = deque(maxlen=100)
start_time = datetime.now()

# ==================== توابع سریع جمع‌آوری پروکسی ====================

def fast_scrap(sources, _proxy_type):
    """جمع‌آوری سریع پروکسی بدون اعتبارسنجی اولیه"""
    for source in sources:
        if source and source.strip():
            try:
                response = requests.get(source.strip(), timeout=10, headers={'User-Agent': get_ua()})
                if response.status_code == 200:
                    # استخراج سریع پروکسی‌ها
                    for line in response.text.split('\n'):
                        line = line.strip()
                        if ':' in line and len(line.split(':')) == 2:
                            ip, port = line.split(':')
                            # چک ساده فرمت
                            if ip.count('.') == 3 and port.isdigit() and 1 <= int(port) <= 65535:
                                if _proxy_type == 'http':
                                    http_proxies.append(line)
                                elif _proxy_type == 'socks4':
                                    socks4_proxies.append(line)
                                elif _proxy_type == 'socks5':
                                    socks5_proxies.append(line)
            except Exception as e:
                errors.write(f'{datetime.now()} - Fast scrap error: {e}\n')

def start_fast_scrap():
    """شروع جمع‌آوری سریع"""
    threads = []
    
    # پاک کردن لیست‌ها
    http_proxies.clear()
    socks4_proxies.clear()
    socks5_proxies.clear()
    
    sources_list = [
        (http.get("Sources").splitlines() if http else [], 'http'),
        (socks4.get("Sources").splitlines() if socks4 else [], 'socks4'),
        (socks5.get("Sources").splitlines() if socks5 else [], 'socks5')
    ]
    
    for sources, ptype in sources_list:
        if sources:
            thread = Thread(target=fast_scrap, args=(sources, ptype))
            threads.append(thread)
            thread.start()
    
    for t in threads:
        t.join(timeout=20)  # حداکثر 20 ثانیه صبر کن
    
    # حذف تکراری‌ها
    global http_proxies, socks4_proxies, socks5_proxies
    http_proxies = list(set(http_proxies))[:max_proxies_per_type]
    socks4_proxies = list(set(socks4_proxies))[:max_proxies_per_type]
    socks5_proxies = list(set(socks5_proxies))[:max_proxies_per_type]

def validate_proxy_quick(proxy, proxy_type):
    """اعتبارسنجی سریع پروکسی"""
    try:
        test_url = "http://httpbin.org/ip"
        proxies = {
            'http': f'{proxy_type}://{proxy}',
            'https': f'{proxy_type}://{proxy}'
        }
        response = requests.get(test_url, proxies=proxies, timeout=2)
        return response.status_code == 200
    except:
        return False

# ==================== توابع اصلی ویو زدن ====================

def get_token(proxy, proxy_type):
    """گرفتن توکن ویو"""
    try:
        session = requests.Session()
        current_ua = get_ua()
        
        response = session.get(
            f'https://t.me/{channel}/{post}',
            params={'embed': '1', 'mode': 'tme'},
            headers={
                'referer': f'https://t.me/{channel}/{post}',
                'user-agent': current_ua
            },
            proxies={
                'http': f'{proxy_type}://{proxy}',
                'https': f'{proxy_type}://{proxy}'
            },
            timeout=time_out)

        token = search(r'data-view="(\d+)"', response.text)
        if token:
            return token.group(1), session
        return None

    except:
        return None

def send_view(token, session, proxy, proxy_type):
    """ارسال ویو"""
    global total_views_sent, successful_views, view_history
    
    try:
        cookies = session.cookies.get_dict()
        
        response = session.get(
            'https://t.me/v/',
            params={'views': token},
            cookies={
                'stel_ssid': cookies.get('stel_ssid', '')
            },
            headers={
                'referer': f'https://t.me/{channel}/{post}?embed=1&mode=tme',
                'user-agent': get_ua(),
                'x-requested-with': 'XMLHttpRequest'
            },
            proxies={
                'http': f'{proxy_type}://{proxy}',
                'https': f'{proxy_type}://{proxy}'
            },
            timeout=time_out)

        total_views_sent += 1
        view_history.append(time.time())
        
        if response.status_code == 200 and response.text.strip() == 'true':
            successful_views += 1
            return True
        return False

    except:
        return False

def worker():
    """کارگر اصلی"""
    global proxy_errors, token_errors
    
    while True:
        try:
            # انتخاب یه پروکسی تصادفی
            if http_proxies and random.random() < 0.4:
                proxy = random.choice(http_proxies)
                proxy_type = 'http'
            elif socks5_proxies and random.random() < 0.3:
                proxy = random.choice(socks5_proxies)
                proxy_type = 'socks5'
            elif socks4_proxies:
                proxy = random.choice(socks4_proxies)
                proxy_type = 'socks4'
            else:
                sleep(0.1)
                continue
            
            token_data = get_token(proxy, proxy_type)
            
            if token_data is None:
                token_errors += 1
            else:
                result = send_view(token_data[0], token_data[1], proxy, proxy_type)
                if not result:
                    proxy_errors += 1
                    
        except Exception as e:
            proxy_errors += 1

# ==================== توابع مانیتورینگ ====================

def calculate_speed():
    """محاسبه سرعت"""
    if len(view_history) < 2:
        return 0
    times = list(view_history)
    time_diff = times[-1] - times[0]
    if time_diff > 0:
        return len(times) / time_diff
    return 0

def check_views():
    """چک کردن ویوهای واقعی"""
    global real_views
    
    while True:
        try:
            response = requests.get(
                f'https://t.me/{channel}/{post}',
                params={'embed': '1', 'mode': 'tme'},
                headers={'user-agent': get_ua()},
                timeout=5)

            views = search(r'<span class="tgme_widget_message_views">([^<]+)', response.text)
            if views:
                real_views = views.group(1).strip()
            sleep(3)
        except:
            sleep(5)

def display_stats():
    """نمایش آمار"""
    while True:
        system('cls' if name == 'nt' else 'clear')
        
        elapsed = datetime.now() - start_time
        minutes = int(elapsed.total_seconds() // 60)
        seconds = int(elapsed.total_seconds() % 60)
        
        speed = calculate_speed()
        total_proxies = len(http_proxies) + len(socks4_proxies) + len(socks5_proxies)
        
        # باکس آمار
        print(Fore.CYAN + "╔" + "═" * 60 + "╗")
        print(Fore.CYAN + "║" + Fore.YELLOW + " " * 18 + "🔥 TELEGRAM VIEW BOT 🔥" + " " * 18 + Fore.CYAN + "║")
        print(Fore.CYAN + "╠" + "═" * 60 + "╣")
        
        print(Fore.CYAN + "║ " + Fore.WHITE + f"TARGET".ljust(12) + ":" + Fore.GREEN + f" {channel}/{post}".ljust(40) + Fore.CYAN + "║")
        print(Fore.CYAN + "║ " + Fore.WHITE + f"VIEWS".ljust(12) + ":" + Fore.GREEN + f" {real_views}".ljust(40) + Fore.CYAN + "║")
        
        print(Fore.CYAN + "╠" + "═" * 60 + "╣")
        
        print(Fore.CYAN + "║ " + Fore.GREEN + f"✅ SUCCESS".ljust(15) + f": {successful_views:>8,}" + 
              " " * 10 + Fore.CYAN + "│" + Fore.YELLOW + f" TOTAL".ljust(10) + f": {total_views_sent:>8,}" + " " * 5 + Fore.CYAN + "║")
        print(Fore.CYAN + "║ " + Fore.RED + f"❌ ERRORS".ljust(15) + f": {proxy_errors + token_errors:>8,}" + 
              " " * 10 + Fore.CYAN + "│" + Fore.MAGENTA + f" SPEED".ljust(10) + f": {speed:>5.1f}/s" + " " * 7 + Fore.CYAN + "║")
        
        print(Fore.CYAN + "╠" + "═" * 60 + "╣")
        
        print(Fore.CYAN + "║ " + Fore.CYAN + f"PROXIES".ljust(60) + "║")
        print(Fore.CYAN + "║ " + Fore.WHITE + f"  HTTP  : {len(http_proxies):>5,}".ljust(25) + 
              Fore.WHITE + f"SOCKS4 : {len(socks4_proxies):>5,}".ljust(20) + 
              Fore.WHITE + f"SOCKS5 : {len(socks5_proxies):>5,}".ljust(15) + Fore.CYAN + "║")
        print(Fore.CYAN + "║ " + Fore.YELLOW + f"  TOTAL PROXIES: {total_proxies:,}".ljust(55) + Fore.CYAN + "║")
        
        print(Fore.CYAN + "╠" + "═" * 60 + "╣")
        
        print(Fore.CYAN + "║ " + Fore.WHITE + f"TIME".ljust(10) + f": {minutes:02d}:{seconds:02d}".ljust(15) + 
              Fore.WHITE + f"THREADS".ljust(12) + f": {active_count():>3,}/{THREADS}".ljust(17) + Fore.CYAN + "║")
        
        print(Fore.CYAN + "╚" + "═" * 60 + "╝")
        
        # وضعیت
        if speed > 20:
            print(Fore.RED + "🚀 INSANE MODE")
        elif speed > 10:
            print(Fore.MAGENTA + "⚡ TURBO MODE")
        elif speed > 0:
            print(Fore.GREEN + "✅ WORKING")
        else:
            print(Fore.YELLOW + "⏳ COLLECTING PROXIES...")
        
        sleep(1.5)

# ==================== شروع ====================

def main():
    global channel, post
    
    print(Fore.CYAN + """
╔════════════════════════════════════════════════════╗
║     🔥 TELEGRAM VIEW BOT - FAST EDITION 🔥       ║
╚════════════════════════════════════════════════════╝
""")
    
    url = input(Fore.YELLOW + "📌 Enter URL: " + Fore.WHITE).strip()
    
    try:
        channel, post = url.replace('https://t.me/', '').split('/')
        post = int(post)
    except:
        print(Fore.RED + "❌ Invalid URL!")
        return
    
    print(Fore.GREEN + f"\n✅ Target: {channel}/{post}")
    print(Fore.CYAN + "📡 Collecting proxies...")
    
    # جمع‌آوری سریع
    start_fast_scrap()
    
    print(Fore.GREEN + f"✅ HTTP: {len(http_proxies)} | SOCKS4: {len(socks4_proxies)} | SOCKS5: {len(socks5_proxies)}")
    print(Fore.YELLOW + "🚀 Starting workers...")
    
    # شروع تردها
    for i in range(THREADS):
        Thread(target=worker, daemon=True).start()
    
    Thread(target=check_views, daemon=True).start()
    display_stats()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(Fore.RED + "\n\n⚠️ Stopped")
        print(Fore.GREEN + f"✅ Total Views: {successful_views:,}")
        errors.close()
