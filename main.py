"""
TELEGRAM VIEW BOT - WORKING VERSION
"""

import os
import sys
import time
import random
import threading
from datetime import datetime
from threading import Thread, active_count
from re import search, compile
from collections import deque

# نصب خودکار
required_packages = ['requests', 'configparser', 'fake-useragent', 'colorama']
for package in required_packages:
    try:
        __import__(package.replace('-', '_'))
    except ImportError:
        os.system(f'pip install {package} -q')

import requests
from time import sleep
from configparser import ConfigParser
from os import system, name
from fake_useragent import UserAgent
from colorama import init, Fore, Style

init(autoreset=True)

# ==================== تنظیمات ====================
THREADS = 200  # کمتر برای شروع
PROXIES_TYPES = ('http', 'socks4', 'socks5')
time_out = 15  # بیشتر برای موفقیت
max_proxies_per_type = 2000

# ==================== User-Agent ====================
try:
    ua = UserAgent()
    def get_ua(): return ua.random
except:
    USER_AGENTS = ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36']
    def get_ua(): return random.choice(USER_AGENTS)

# ==================== Regex ====================
REGEX = compile(r"(?:^|\D)?(("+ r"(?:[1-9]|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"):" + (r"(?:\d|[1-9]\d{1,3}|[1-5]\d{4}|6[0-4]\d{3}"
                + r"|65[0-4]\d{2}|655[0-2]\d|6553[0-5])")
                + r")(?:\D|$)")

# ==================== فایل خطا ====================
errors = open('errors.txt', 'a+', encoding='utf-8')

# ==================== config.ini ====================
cfg = ConfigParser()
cfg.read("config.ini", encoding="utf-8")

try:
    http = cfg["HTTP"]
    socks4 = cfg["SOCKS4"]
    socks5 = cfg["SOCKS5"]
except:
    print(Fore.RED + "config.ini not found!")
    exit()

# ==================== متغیرها ====================
http_proxies = []
socks4_proxies = []
socks5_proxies = []
proxy_errors = 0
token_errors = 0
total_views = 0
successful_views = 0
channel = ''
post = 0
real_views = '0'
working_proxies = []
start_time = datetime.now()

# ==================== جمع‌آوری پروکسی ====================

def collect_proxies(sources, proxy_type):
    """جمع‌آوری پروکسی"""
    for source in sources:
        if source and source.strip():
            try:
                r = requests.get(source.strip(), timeout=10)
                if r.status_code == 200:
                    for line in r.text.split('\n'):
                        line = line.strip()
                        if ':' in line and line.count('.') == 3:
                            if proxy_type == 'http':
                                http_proxies.append(line)
                            elif proxy_type == 'socks4':
                                socks4_proxies.append(line)
                            elif proxy_type == 'socks5':
                                socks5_proxies.append(line)
            except:
                pass

def start_collection():
    """شروع جمع‌آوری"""
    threads = []
    
    http_proxies.clear()
    socks4_proxies.clear()
    socks5_proxies.clear()
    
    sources = [
        (http.get("Sources").splitlines(), 'http'),
        (socks4.get("Sources").splitlines(), 'socks4'),
        (socks5.get("Sources").splitlines(), 'socks5')
    ]
    
    for src, ptype in sources:
        t = Thread(target=collect_proxies, args=(src, ptype))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join(timeout=15)
    
    # حذف تکراری
    http_proxies[:] = list(set(http_proxies))[:1000]
    socks4_proxies[:] = list(set(socks4_proxies))[:1000]
    socks5_proxies[:] = list(set(socks5_proxies))[:1000]
    
    print(Fore.GREEN + f"📡 HTTP: {len(http_proxies)} | SOCKS4: {len(socks4_proxies)} | SOCKS5: {len(socks5_proxies)}")

# ==================== تست پروکسی ====================

def test_proxy(proxy, proxy_type):
    """تست اینکه پروکسی کار میکنه"""
    try:
        test_url = "http://httpbin.org/ip"
        proxies = {
            'http': f'{proxy_type}://{proxy}',
            'https': f'{proxy_type}://{proxy}'
        }
        r = requests.get(test_url, proxies=proxies, timeout=5)
        return r.status_code == 200
    except:
        return False

def filter_working_proxies():
    """فقط پروکسی‌های کارآمد رو نگه دار"""
    global http_proxies, socks4_proxies, socks5_proxies
    
    print(Fore.YELLOW + "🔍 Testing proxies (this may take a minute)...")
    
    working_http = []
    for proxy in http_proxies[:200]:
        if test_proxy(proxy, 'http'):
            working_http.append(proxy)
    
    working_socks4 = []
    for proxy in socks4_proxies[:200]:
        if test_proxy(proxy, 'socks4'):
            working_socks4.append(proxy)
    
    working_socks5 = []
    for proxy in socks5_proxies[:200]:
        if test_proxy(proxy, 'socks5'):
            working_socks5.append(proxy)
    
    http_proxies = working_http
    socks4_proxies = working_socks4
    socks5_proxies = working_socks5
    
    total = len(http_proxies) + len(socks4_proxies) + len(socks5_proxies)
    print(Fore.GREEN + f"✅ Working proxies: {total}")
    return total > 0

# ==================== ویو زدن ====================

def send_view_request(proxy, proxy_type):
    """ارسال یک ویو"""
    global total_views, successful_views, proxy_errors, token_errors
    
    try:
        session = requests.Session()
        
        # گرفتن توکن
        r1 = session.get(
            f'https://t.me/{channel}/{post}',
            params={'embed': '1', 'mode': 'tme'},
            headers={'user-agent': get_ua()},
            proxies={
                'http': f'{proxy_type}://{proxy}',
                'https': f'{proxy_type}://{proxy}'
            },
            timeout=time_out)
        
        token = search(r'data-view="(\d+)"', r1.text)
        if not token:
            token_errors += 1
            return False
        
        # ارسال ویو
        r2 = session.get(
            'https://t.me/v/',
            params={'views': token.group(1)},
            headers={
                'user-agent': get_ua(),
                'x-requested-with': 'XMLHttpRequest'
            },
            proxies={
                'http': f'{proxy_type}://{proxy}',
                'https': f'{proxy_type}://{proxy}'
            },
            timeout=time_out)
        
        total_views += 1
        
        if r2.status_code == 200 and 'true' in r2.text:
            successful_views += 1
            return True
        else:
            proxy_errors += 1
            return False
            
    except:
        proxy_errors += 1
        return False

def worker():
    """کارگر"""
    while True:
        try:
            # انتخاب پروکسی
            all_proxies = []
            all_proxies.extend([('http', p) for p in http_proxies])
            all_proxies.extend([('socks4', p) for p in socks4_proxies])
            all_proxies.extend([('socks5', p) for p in socks5_proxies])
            
            if not all_proxies:
                sleep(1)
                continue
            
            proxy_type, proxy = random.choice(all_proxies)
            send_view_request(proxy, proxy_type)
            
        except:
            sleep(0.1)

# ==================== نمایش آمار ====================

def show_stats():
    """نمایش آمار"""
    while True:
        system('cls' if name == 'nt' else 'clear')
        
        elapsed = datetime.now() - start_time
        minutes = int(elapsed.total_seconds() // 60)
        seconds = int(elapsed.total_seconds() % 60)
        
        speed = successful_views / (elapsed.total_seconds() + 0.1)
        total_proxies = len(http_proxies) + len(socks4_proxies) + len(socks5_proxies)
        
        print(Fore.CYAN + "╔" + "═" * 50 + "╗")
        print(Fore.CYAN + "║" + Fore.YELLOW + " " * 15 + "TELEGRAM VIEW BOT" + " " * 15 + Fore.CYAN + "║")
        print(Fore.CYAN + "╠" + "═" * 50 + "╣")
        print(Fore.CYAN + "║ " + Fore.WHITE + f"TARGET".ljust(12) + ":" + Fore.GREEN + f" {channel}/{post}".ljust(30) + Fore.CYAN + "║")
        print(Fore.CYAN + "║ " + Fore.WHITE + f"VIEWS".ljust(12) + ":" + Fore.GREEN + f" {real_views}".ljust(30) + Fore.CYAN + "║")
        print(Fore.CYAN + "╠" + "═" * 50 + "╣")
        print(Fore.CYAN + "║ " + Fore.GREEN + f"✅ SUCCESS".ljust(15) + f": {successful_views:>6,}" + " " * 10 + Fore.CYAN + "║")
        print(Fore.CYAN + "║ " + Fore.YELLOW + f"📦 TOTAL".ljust(15) + f": {total_views:>6,}" + " " * 10 + Fore.CYAN + "║")
        print(Fore.CYAN + "║ " + Fore.RED + f"❌ ERRORS".ljust(15) + f": {proxy_errors + token_errors:>6,}" + " " * 10 + Fore.CYAN + "║")
        print(Fore.CYAN + "║ " + Fore.MAGENTA + f"⚡ SPEED".ljust(15) + f": {speed:>5.1f}/s" + " " * 11 + Fore.CYAN + "║")
        print(Fore.CYAN + "╠" + "═" * 50 + "╣")
        print(Fore.CYAN + "║ " + Fore.CYAN + f"PROXIES".ljust(50) + "║")
        print(Fore.CYAN + "║ " + Fore.WHITE + f"HTTP: {len(http_proxies)} | SOCKS4: {len(socks4_proxies)} | SOCKS5: {len(socks5_proxies)}".ljust(48) + Fore.CYAN + "║")
        print(Fore.CYAN + "╠" + "═" * 50 + "╣")
        print(Fore.CYAN + "║ " + Fore.WHITE + f"TIME: {minutes:02d}:{seconds:02d}".ljust(25) + f"THREADS: {active_count()}/{THREADS}".ljust(23) + Fore.CYAN + "║")
        print(Fore.CYAN + "╚" + "═" * 50 + "╝")
        
        sleep(2)

def check_real_views():
    """چک کردن ویو واقعی"""
    global real_views
    while True:
        try:
            r = requests.get(f'https://t.me/{channel}/{post}', params={'embed': '1'}, timeout=5)
            views = search(r'<span class="tgme_widget_message_views">([^<]+)', r.text)
            if views:
                real_views = views.group(1)
            sleep(3)
        except:
            sleep(5)

# ==================== شروع ====================

def main():
    global channel, post
    
    system('cls' if name == 'nt' else 'clear')
    
    print(Fore.CYAN + "╔════════════════════════════════════╗")
    print(Fore.CYAN + "║     TELEGRAM VIEW BOT v2.0        ║")
    print(Fore.CYAN + "╚════════════════════════════════════╝")
    
    url = input(Fore.YELLOW + "URL: " + Fore.WHITE).strip()
    
    try:
        channel, post = url.replace('https://t.me/', '').split('/')
        post = int(post)
    except:
        print(Fore.RED + "Invalid URL!")
        return
    
    print(Fore.GREEN + f"\n✅ Target: {channel}/{post}")
    print(Fore.CYAN + "📡 Collecting proxies...")
    
    start_collection()
    
    print(Fore.YELLOW + "🔍 Filtering working proxies...")
    if not filter_working_proxies():
        print(Fore.RED + "❌ No working proxies found!")
        return
    
    print(Fore.GREEN + "🚀 Starting workers...")
    
    # شروع تردها
    for i in range(THREADS):
        Thread(target=worker, daemon=True).start()
    
    Thread(target=check_real_views, daemon=True).start()
    show_stats()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(Fore.RED + "\nStopped")
        errors.close()
