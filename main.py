"""
TELEGRAM VIEW BOT - DEBUG VERSION
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
THREADS = 100  # کمتر برای شروع
PROXIES_TYPES = ('http', 'socks4', 'socks5')
time_out = 20  # بیشتر
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

errors = open('errors.txt', 'a+', encoding='utf-8')

# ==================== بارگذاری config.ini ====================
print(Fore.CYAN + "\n📂 Loading config.ini...")
cfg = ConfigParser()
cfg.read("config.ini", encoding="utf-8")

try:
    http = cfg["HTTP"]
    socks4 = cfg["SOCKS4"]
    socks5 = cfg["SOCKS5"]
    
    http_sources = [s.strip() for s in http.get("Sources").split('\n') if s.strip()]
    socks4_sources = [s.strip() for s in socks4.get("Sources").split('\n') if s.strip()]
    socks5_sources = [s.strip() for s in socks5.get("Sources").split('\n') if s.strip()]
    
except Exception as e:
    print(Fore.RED + f"❌ Error: {e}")
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
start_time = datetime.now()

# ==================== جمع‌آوری پروکسی ====================

def collect_from_url(url, proxy_type):
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
        errors.write(f'{datetime.now()} - {url}: {e}\n')

def collect_all():
    print(Fore.YELLOW + "\n📡 Collecting proxies...")
    threads = []
    
    for url in http_sources:
        t = Thread(target=collect_from_url, args=(url, 'http'))
        threads.append(t)
        t.start()
    
    for url in socks4_sources:
        t = Thread(target=collect_from_url, args=(url, 'socks4'))
        threads.append(t)
        t.start()
    
    for url in socks5_sources:
        t = Thread(target=collect_from_url, args=(url, 'socks5'))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join(timeout=15)
    
    # Remove duplicates
    http_proxies[:] = list(set(http_proxies))
    socks4_proxies[:] = list(set(socks4_proxies))
    socks5_proxies[:] = list(set(socks5_proxies))
    
    print(Fore.CYAN + "\n" + "="*50)
    print(Fore.GREEN + f"📊 TOTAL PROXIES:")
    print(Fore.GREEN + f"   HTTP  : {len(http_proxies):,}")
    print(Fore.GREEN + f"   SOCKS4: {len(socks4_proxies):,}")
    print(Fore.GREEN + f"   SOCKS5: {len(socks5_proxies):,}")
    print(Fore.CYAN + "="*50)

# ==================== تست پروکسی (با دیباگ) ====================

def test_proxy(proxy, proxy_type, index, total):
    """تست با نمایش پیشرفت"""
    try:
        test_url = "http://httpbin.org/ip"
        proxies = {
            'http': f'{proxy_type}://{proxy}',
            'https': f'{proxy_type}://{proxy}'
        }
        start = time.time()
        r = requests.get(test_url, proxies=proxies, timeout=5)
        elapsed = time.time() - start
        
        if r.status_code == 200:
            print(Fore.GREEN + f"   ✅ [{index}/{total}] {proxy_type}://{proxy} - {elapsed:.1f}s")
            return True
        else:
            print(Fore.RED + f"   ❌ [{index}/{total}] {proxy_type}://{proxy} - {r.status_code}")
            return False
    except Exception as e:
        print(Fore.RED + f"   ❌ [{index}/{total}] {proxy_type}://{proxy} - {str(e)[:30]}")
        return False

def filter_proxies():
    """فیلتر با نمایش پیشرفت"""
    global http_proxies, socks4_proxies, socks5_proxies
    
    print(Fore.YELLOW + "\n🔍 Testing proxies (this may take a few minutes)...")
    
    working_http = []
    total_http = len(http_proxies)
    for i, proxy in enumerate(http_proxies[:200]):  # فقط 200 تا برای شروع
        if test_proxy(proxy, 'http', i+1, total_http):
            working_http.append(proxy)
    
    working_socks4 = []
    total_socks4 = len(socks4_proxies)
    for i, proxy in enumerate(socks4_proxies[:200]):
        if test_proxy(proxy, 'socks4', i+1, total_socks4):
            working_socks4.append(proxy)
    
    working_socks5 = []
    total_socks5 = len(socks5_proxies)
    for i, proxy in enumerate(socks5_proxies[:200]):
        if test_proxy(proxy, 'socks5', i+1, total_socks5):
            working_socks5.append(proxy)
    
    http_proxies = working_http
    socks4_proxies = working_socks4
    socks5_proxies = working_socks5
    
    total = len(http_proxies) + len(socks4_proxies) + len(socks5_proxies)
    print(Fore.GREEN + f"\n✅ Working proxies: {total}")
    return total > 0

# ==================== ویو زدن ====================

def send_view(proxy, proxy_type):
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
    while True:
        try:
            all_proxies = []
            for p in http_proxies:
                all_proxies.append(('http', p))
            for p in socks4_proxies:
                all_proxies.append(('socks4', p))
            for p in socks5_proxies:
                all_proxies.append(('socks5', p))
            
            if not all_proxies:
                sleep(1)
                continue
            
            proxy_type, proxy = random.choice(all_proxies)
            send_view(proxy, proxy_type)
            sleep(0.05)
            
        except:
            sleep(0.1)

# ==================== آمار ساده ====================

def show_stats():
    while True:
        system('cls' if name == 'nt' else 'clear')
        
        elapsed = datetime.now() - start_time
        minutes = int(elapsed.total_seconds() // 60)
        seconds = int(elapsed.total_seconds() % 60)
        
        speed = successful_views / (elapsed.total_seconds() + 0.1)
        total_proxies = len(http_proxies) + len(socks4_proxies) + len(socks5_proxies)
        
        print(Fore.CYAN + "="*60)
        print(Fore.YELLOW + "           TELEGRAM VIEW BOT")
        print(Fore.CYAN + "="*60)
        print(Fore.WHITE + f"Target: {channel}/{post}")
        print(Fore.WHITE + f"Current Views: {real_views}")
        print(Fore.CYAN + "-"*60)
        print(Fore.GREEN + f"✅ Success: {successful_views}")
        print(Fore.YELLOW + f"📦 Total: {total_views}")
        print(Fore.RED + f"❌ Errors: {proxy_errors + token_errors}")
        print(Fore.CYAN + "-"*60)
        print(Fore.MAGENTA + f"⚡ Speed: {speed:.1f}/s")
        print(Fore.WHITE + f"⏱️ Time: {minutes:02d}:{seconds:02d}")
        print(Fore.CYAN + "-"*60)
        print(Fore.CYAN + f"Proxies: HTTP:{len(http_proxies)} SOCKS4:{len(socks4_proxies)} SOCKS5:{len(socks5_proxies)}")
        print(Fore.WHITE + f"Threads: {active_count()}/{THREADS}")
        print(Fore.CYAN + "="*60)
        
        sleep(2)

def check_views():
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
╔════════════════════════════════════════════════════╗
║     TELEGRAM VIEW BOT - DEBUG MODE                ║
╚════════════════════════════════════════════════════╝
""")
    
    url = input(Fore.YELLOW + "URL: " + Fore.WHITE).strip()
    
    try:
        channel, post = url.replace('https://t.me/', '').split('/')
        post = int(post)
    except:
        print(Fore.RED + "❌ Invalid URL!")
        return
    
    print(Fore.GREEN + f"\n✅ Target: {channel}/{post}")
    
    collect_all()
    
    if not filter_proxies():
        print(Fore.RED + "\n❌ No working proxies!")
        print(Fore.YELLOW + "Try increasing time_out or use different sources")
        return
    
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
        errors.close()
