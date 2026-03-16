"""
TELEGRAM VIEW BOT - FINAL VERSION WITH YOUR CONFIG
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
THREADS = 300
PROXIES_TYPES = ('http', 'socks4', 'socks5')
time_out = 15
max_proxies_per_type = 3000

# ==================== User-Agent ====================
try:
    ua = UserAgent()
    def get_ua(): return ua.random
except:
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
    ]
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

# ==================== بارگذاری YOUR config.ini ====================
print(Fore.CYAN + "╔════════════════════════════════════════════════════╗")
print(Fore.CYAN + "║     LOADING YOUR PROXY SOURCES...                ║")
print(Fore.CYAN + "╚════════════════════════════════════════════════════╝")

cfg = ConfigParser()
cfg.read("config.ini", encoding="utf-8")

try:
    http = cfg["HTTP"]
    socks4 = cfg["SOCKS4"]
    socks5 = cfg["SOCKS5"]
    
    # نمایش منابع شما
    http_sources = [s.strip() for s in http.get("Sources").split('\n') if s.strip()]
    socks4_sources = [s.strip() for s in socks4.get("Sources").split('\n') if s.strip()]
    socks5_sources = [s.strip() for s in socks5.get("Sources").split('\n') if s.strip()]
    
    print(Fore.GREEN + f"\n✅ HTTP sources: {len(http_sources)}")
    for s in http_sources[:3]:
        print(Fore.CYAN + f"   📍 {s[:50]}...")
    
    print(Fore.GREEN + f"\n✅ SOCKS4 sources: {len(socks4_sources)}")
    for s in socks4_sources[:3]:
        print(Fore.CYAN + f"   📍 {s[:50]}...")
    
    print(Fore.GREEN + f"\n✅ SOCKS5 sources: {len(socks5_sources)}")
    for s in socks5_sources[:3]:
        print(Fore.CYAN + f"   📍 {s[:50]}...")
    
except Exception as e:
    print(Fore.RED + f"❌ Error reading config.ini: {e}")
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

def collect_from_url(url, proxy_type):
    """جمع‌آوری از یک URL"""
    try:
        headers = {'User-Agent': get_ua()}
        r = requests.get(url, timeout=10, headers=headers)
        if r.status_code == 200:
            count = 0
            for line in r.text.split('\n'):
                line = line.strip()
                if ':' in line and line.count('.') == 3:
                    parts = line.split(':')
                    if len(parts) == 2 and parts[1].isdigit():
                        if proxy_type == 'http':
                            http_proxies.append(line)
                        elif proxy_type == 'socks4':
                            socks4_proxies.append(line)
                        elif proxy_type == 'socks5':
                            socks5_proxies.append(line)
                        count += 1
            print(Fore.GREEN + f"   ✅ +{count} from {url.split('/')[-1][:20]}")
    except Exception as e:
        errors.write(f'{datetime.now()} - Collect error {url}: {e}\n')

def collect_all():
    """جمع‌آوری از همه منابع"""
    print(Fore.YELLOW + "\n📡 Collecting proxies from your sources...")
    
    threads = []
    
    # HTTP
    for url in http_sources:
        t = Thread(target=collect_from_url, args=(url, 'http'))
        threads.append(t)
        t.start()
    
    # SOCKS4
    for url in socks4_sources:
        t = Thread(target=collect_from_url, args=(url, 'socks4'))
        threads.append(t)
        t.start()
    
    # SOCKS5
    for url in socks5_sources:
        t = Thread(target=collect_from_url, args=(url, 'socks5'))
        threads.append(t)
        t.start()
    
    # Wait
    for t in threads:
        t.join(timeout=20)
    
    # Remove duplicates
    http_proxies[:] = list(set(http_proxies))
    socks4_proxies[:] = list(set(socks4_proxies))
    socks5_proxies[:] = list(set(socks5_proxies))
    
    print(Fore.CYAN + "\n" + "="*50)
    print(Fore.GREEN + f"📊 TOTAL PROXIES COLLECTED:")
    print(Fore.GREEN + f"   HTTP  : {len(http_proxies):,}")
    print(Fore.GREEN + f"   SOCKS4: {len(socks4_proxies):,}")
    print(Fore.GREEN + f"   SOCKS5: {len(socks5_proxies):,}")
    print(Fore.CYAN + "="*50)

# ==================== تست سریع پروکسی ====================

def test_proxy(proxy, proxy_type):
    """تست یک پروکسی"""
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

def filter_proxies():
    """فقط پروکسی‌های کارآمد"""
    global http_proxies, socks4_proxies, socks5_proxies
    
    print(Fore.YELLOW + "\n🔍 Testing proxies (30 seconds)...")
    
    # HTTP
    working_http = []
    for proxy in http_proxies[:300]:
        if test_proxy(proxy, 'http'):
            working_http.append(proxy)
    
    # SOCKS4
    working_socks4 = []
    for proxy in socks4_proxies[:300]:
        if test_proxy(proxy, 'socks4'):
            working_socks4.append(proxy)
    
    # SOCKS5
    working_socks5 = []
    for proxy in socks5_proxies[:300]:
        if test_proxy(proxy, 'socks5'):
            working_socks5.append(proxy)
    
    http_proxies = working_http
    socks4_proxies = working_socks4
    socks5_proxies = working_socks5
    
    total = len(http_proxies) + len(socks4_proxies) + len(socks5_proxies)
    print(Fore.GREEN + f"✅ Working proxies: {total}")
    return total > 0

# ==================== ویو زدن ====================

def send_view(proxy, proxy_type):
    """ارسال ویو"""
    global total_views, successful_views, proxy_errors, token_errors
    
    try:
        session = requests.Session()
        
        # Get token
        r1 = session.get(
            f'https://t.me/{channel}/{post}',
            params={'embed': '1', 'mode': 'tme'},
            headers={
                'referer': f'https://t.me/{channel}/{post}',
                'user-agent': get_ua()
            },
            proxies={
                'http': f'{proxy_type}://{proxy}',
                'https': f'{proxy_type}://{proxy}'
            },
            timeout=time_out)
        
        if r1.status_code != 200:
            proxy_errors += 1
            return False
        
        token = search(r'data-view="(\d+)"', r1.text)
        if not token:
            token_errors += 1
            return False
        
        # Send view
        r2 = session.get(
            'https://t.me/v/',
            params={'views': token.group(1)},
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
        
        total_views += 1
        
        if r2.status_code == 200 and 'true' in r2.text.lower():
            successful_views += 1
            return True
        else:
            proxy_errors += 1
            return False
            
    except Exception as e:
        proxy_errors += 1
        return False

def worker():
    """کارگر"""
    while True:
        try:
            # جمع کردن همه پروکسی‌ها
            all_proxies = []
            for p in http_proxies:
                all_proxies.append(('http', p))
            for p in socks4_proxies:
                all_proxies.append(('socks4', p))
            for p in socks5_proxies:
                all_proxies.append(('socks5', p))
            
            if not all_proxies:
                sleep(0.5)
                continue
            
            proxy_type, proxy = random.choice(all_proxies)
            send_view(proxy, proxy_type)
            sleep(0.02)
            
        except:
            sleep(0.1)

# ==================== آمار ====================

def show_stats():
    """نمایش آمار"""
    while True:
        system('cls' if name == 'nt' else 'clear')
        
        elapsed = datetime.now() - start_time
        minutes = int(elapsed.total_seconds() // 60)
        seconds = int(elapsed.total_seconds() % 60)
        
        speed = successful_views / (elapsed.total_seconds() + 0.1)
        total_proxies = len(http_proxies) + len(socks4_proxies) + len(socks5_proxies)
        
        print(Fore.CYAN + "╔" + "═" * 60 + "╗")
        print(Fore.CYAN + "║" + Fore.YELLOW + " " * 18 + "🔥 TELEGRAM VIEW BOT 🔥" + " " * 18 + Fore.CYAN + "║")
        print(Fore.CYAN + "╠" + "═" * 60 + "╣")
        print(Fore.CYAN + "║ " + Fore.WHITE + "TARGET".ljust(12) + ":" + Fore.GREEN + f" {channel}/{post}".ljust(42) + Fore.CYAN + "║")
        print(Fore.CYAN + "║ " + Fore.WHITE + "CURRENT".ljust(12) + ":" + Fore.GREEN + f" {real_views}".ljust(42) + Fore.CYAN + "║")
        print(Fore.CYAN + "╠" + "═" * 60 + "╣")
        print(Fore.CYAN + "║ " + Fore.GREEN + "✅ SUCCESS".ljust(20) + f": {successful_views:>8,}" + " " * 26 + Fore.CYAN + "║")
        print(Fore.CYAN + "║ " + Fore.YELLOW + "📦 TOTAL".ljust(20) + f": {total_views:>8,}" + " " * 26 + Fore.CYAN + "║")
        print(Fore.CYAN + "║ " + Fore.RED + "❌ PROXY ERR".ljust(20) + f": {proxy_errors:>8,}" + " " * 26 + Fore.CYAN + "║")
        print(Fore.CYAN + "║ " + Fore.RED + "⚠️ TOKEN ERR".ljust(20) + f": {token_errors:>8,}" + " " * 26 + Fore.CYAN + "║")
        print(Fore.CYAN + "╠" + "═" * 60 + "╣")
        print(Fore.CYAN + "║ " + Fore.MAGENTA + "⚡ SPEED".ljust(20) + f": {speed:.2f}/s".ljust(34) + Fore.CYAN + "║")
        print(Fore.CYAN + "║ " + Fore.WHITE + "⏱️ TIME".ljust(20) + f": {minutes:02d}:{seconds:02d}".ljust(34) + Fore.CYAN + "║")
        print(Fore.CYAN + "╠" + "═" * 60 + "╣")
        print(Fore.CYAN + "║ " + Fore.CYAN + "📊 PROXIES".ljust(60) + "║")
        print(Fore.CYAN + "║ " + Fore.WHITE + f"HTTP: {len(http_proxies):>4} | SOCKS4: {len(socks4_proxies):>4} | SOCKS5: {len(socks5_proxies):>4} | TOTAL: {total_proxies:>4}".ljust(58) + Fore.CYAN + "║")
        print(Fore.CYAN + "╠" + "═" * 60 + "╣")
        print(Fore.CYAN + "║ " + Fore.WHITE + f"THREADS: {active_count():>3}/{THREADS}".ljust(58) + Fore.CYAN + "║")
        print(Fore.CYAN + "╚" + "═" * 60 + "╝")
        
        sleep(2)

def check_views():
    """چک ویو"""
    global real_views
    while True:
        try:
            r = requests.get(
                f'https://t.me/{channel}/{post}',
                params={'embed': '1'},
                headers={'user-agent': get_ua()},
                timeout=5
            )
            views = search(r'<span class="tgme_widget_message_views">([^<]+)', r.text)
            if views:
                real_views = views.group(1)
            sleep(3)
        except:
            sleep(5)

# ==================== MAIN ====================

def main():
    global channel, post
    
    system('cls' if name == 'nt' else 'clear')
    
    print(Fore.CYAN + """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     🔥 TELEGRAM VIEW BOT - POWERED BY YOUR CONFIG 🔥       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    url = input(Fore.YELLOW + "📌 Enter Telegram URL: " + Fore.WHITE).strip()
    
    try:
        channel, post = url.replace('https://t.me/', '').split('/')
        post = int(post)
    except:
        print(Fore.RED + "❌ Invalid URL! Use: https://t.me/username/123")
        return
    
    print(Fore.GREEN + f"\n✅ Target: {channel}/{post}")
    
    # جمع‌آوری
    collect_all()
    
    # فیلتر
    if not filter_proxies():
        print(Fore.RED + "\n❌ No working proxies!")
        return
    
    # شروع
    print(Fore.GREEN + "\n🚀 Starting workers...")
    for i in range(THREADS):
        Thread(target=worker, daemon=True).start()
    
    Thread(target=check_views, daemon=True).start()
    show_stats()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(Fore.RED + "\n\n⚠️ Stopped")
        print(Fore.GREEN + f"✅ Final Views: {successful_views}")
        errors.close()
