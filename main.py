"""
TELEGRAM VIEW BOT - WITH BETTER PROXY SOURCES
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
THREADS = 200
time_out = 15

# ==================== User-Agent ====================
try:
    ua = UserAgent()
    def get_ua(): return ua.random
except:
    USER_AGENTS = ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36']
    def get_ua(): return random.choice(USER_AGENTS)

# ==================== منابع جدید و فعال ====================
PROXY_SOURCES = {
    'http': [
        'https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt',
        'https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt',
        'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
        'https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt',
        'https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt',
    ],
    'socks4': [
        'https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt',
        'https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks4.txt',
        'https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks4.txt',
        'https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks4.txt',
    ],
    'socks5': [
        'https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt',
        'https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks5.txt',
        'https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt',
        'https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt',
        'https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt',
    ]
}

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
errors = open('errors.txt', 'a+', encoding='utf-8')

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
        pass

def collect_all():
    print(Fore.YELLOW + "\n📡 Collecting fresh proxies...")
    threads = []
    
    for url in PROXY_SOURCES['http']:
        t = Thread(target=collect_from_url, args=(url, 'http'))
        threads.append(t)
        t.start()
    
    for url in PROXY_SOURCES['socks4']:
        t = Thread(target=collect_from_url, args=(url, 'socks4'))
        threads.append(t)
        t.start()
    
    for url in PROXY_SOURCES['socks5']:
        t = Thread(target=collect_from_url, args=(url, 'socks5'))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join(timeout=15)
    
    # حذف تکراری
    http_proxies[:] = list(set(http_proxies))
    socks4_proxies[:] = list(set(socks4_proxies))
    socks5_proxies[:] = list(set(socks5_proxies))
    
    print(Fore.CYAN + "\n" + "="*50)
    print(Fore.GREEN + f"📊 TOTAL PROXIES:")
    print(Fore.GREEN + f"   HTTP  : {len(http_proxies):,}")
    print(Fore.GREEN + f"   SOCKS4: {len(socks4_proxies):,}")
    print(Fore.GREEN + f"   SOCKS5: {len(socks5_proxies):,}")
    print(Fore.CYAN + "="*50)

# ==================== تست سریع ====================

def quick_test(proxy, proxy_type):
    """تست سریع بدون نمایش"""
    try:
        test_url = "http://httpbin.org/ip"
        proxies = {
            'http': f'{proxy_type}://{proxy}',
            'https': f'{proxy_type}://{proxy}'
        }
        r = requests.get(test_url, proxies=proxies, timeout=3)
        return r.status_code == 200
    except:
        return False

def filter_quick():
    """فیلتر سریع"""
    global http_proxies, socks4_proxies, socks5_proxies
    
    print(Fore.YELLOW + "\n⚡ Quick testing proxies...")
    
    working_http = []
    for proxy in http_proxies[:500]:
        if quick_test(proxy, 'http'):
            working_http.append(proxy)
    
    working_socks4 = []
    for proxy in socks4_proxies[:500]:
        if quick_test(proxy, 'socks4'):
            working_socks4.append(proxy)
    
    working_socks5 = []
    for proxy in socks5_proxies[:500]:
        if quick_test(proxy, 'socks5'):
            working_socks5.append(proxy)
    
    http_proxies = working_http
    socks4_proxies = working_socks4
    socks5_proxies = working_socks5
    
    total = len(http_proxies) + len(socks4_proxies) + len(socks5_proxies)
    print(Fore.GREEN + f"✅ Working proxies: {total}")
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

# ==================== آمار ====================

def show_stats():
    while True:
        system('cls' if name == 'nt' else 'clear')
        
        elapsed = datetime.now() - start_time
        minutes = int(elapsed.total_seconds() // 60)
        seconds = int(elapsed.total_seconds() % 60)
        
        speed = successful_views / (elapsed.total_seconds() + 0.1)
        total_proxies = len(http_proxies) + len(socks4_proxies) + len(socks5_proxies)
        
        print(Fore.CYAN + "╔" + "═" * 60 + "╗")
        print(Fore.CYAN + "║" + Fore.YELLOW + " " * 18 + "TELEGRAM VIEW BOT" + " " * 19 + Fore.CYAN + "║")
        print(Fore.CYAN + "╠" + "═" * 60 + "╣")
        print(Fore.CYAN + "║ " + Fore.WHITE + f"TARGET".ljust(12) + ":" + Fore.GREEN + f" {channel}/{post}".ljust(42) + Fore.CYAN + "║")
        print(Fore.CYAN + "║ " + Fore.WHITE + f"CURRENT".ljust(12) + ":" + Fore.GREEN + f" {real_views}".ljust(42) + Fore.CYAN + "║")
        print(Fore.CYAN + "╠" + "═" * 60 + "╣")
        print(Fore.CYAN + "║ " + Fore.GREEN + f"✅ SUCCESS".ljust(20) + f": {successful_views:>8,}" + " " * 26 + Fore.CYAN + "║")
        print(Fore.CYAN + "║ " + Fore.YELLOW + f"📦 TOTAL".ljust(20) + f": {total_views:>8,}" + " " * 26 + Fore.CYAN + "║")
        print(Fore.CYAN + "║ " + Fore.RED + f"❌ ERRORS".ljust(20) + f": {proxy_errors + token_errors:>8,}" + " " * 26 + Fore.CYAN + "║")
        print(Fore.CYAN + "╠" + "═" * 60 + "╣")
        print(Fore.CYAN + "║ " + Fore.MAGENTA + f"⚡ SPEED".ljust(20) + f": {speed:.1f}/s".ljust(34) + Fore.CYAN + "║")
        print(Fore.CYAN + "║ " + Fore.WHITE + f"⏱️ TIME".ljust(20) + f": {minutes:02d}:{seconds:02d}".ljust(34) + Fore.CYAN + "║")
        print(Fore.CYAN + "╠" + "═" * 60 + "╣")
        print(Fore.CYAN + "║ " + Fore.CYAN + f"PROXIES".ljust(60) + "║")
        print(Fore.CYAN + "║ " + Fore.WHITE + f"HTTP: {len(http_proxies)} | SOCKS4: {len(socks4_proxies)} | SOCKS5: {len(socks5_proxies)} | TOTAL: {total_proxies}".ljust(58) + Fore.CYAN + "║")
        print(Fore.CYAN + "╚" + "═" * 60 + "╝")
        
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
║     TELEGRAM VIEW BOT - FRESH PROXY SOURCES       ║
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
    
    if not filter_quick():
        print(Fore.RED + "\n❌ No working proxies found!")
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
