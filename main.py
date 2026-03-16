#!/usr/bin/env python3
# Telegram View Bot - Proxy Scraper + Viewer
# Reads proxy links from config.ini and scrapes proxies

import os
import re
import sys
from time import sleep
from threading import Thread, active_count, Lock
from configparser import ConfigParser
from os import system, name
import requests

# نصب خودکار ماژول‌ها
try:
    import socks
except:
    os.system('pip install pysocks')
    import socks

# تنظیمات
THREADS = 2000
PROXIES_TYPES = ('http', 'socks4', 'socks5')
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
TIMEOUT = 10

# Regex برای پروکسی (IPv4:Port)
PROXY_REGEX = re.compile(r'(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?):[0-9]{2,5}')

# Regex برای حذف کامنت‌ها در config.ini
COMMENT_REGEX = re.compile(r'^\s*#.*$')

# آمار با قفل
stats_lock = Lock()
stats = {
    'views_sent': 0,
    'working_proxies': 0,
    'total_proxies': 0,
    'failed_proxies': 0,
    'token_errors': 0,
    'scraped_proxies': 0
}

# متغیرهای سراسری
http_proxies, socks4_proxies, socks5_proxies = [], [], []
channel, post = '', 0
running = True

# ========== خواندن config.ini ==========
def read_config():
    """خواندن لینک‌های پروکسی از config.ini"""
    cfg = ConfigParser(interpolation=None)
    
    if not os.path.exists('config.ini'):
        print("[!] config.ini not found!")
        return None
    
    cfg.read("config.ini", encoding="utf-8")
    return cfg

def get_sources_from_config(cfg, section):
    """استخراج لینک‌های منبع از یک بخش خاص با حذف کامنت‌ها"""
    sources = []
    
    if section in cfg:
        # خواندن خط به خط
        for line in cfg[section].get("Sources", "").splitlines():
            line = line.strip()
            
            # حذف کامنت‌ها (خطوطی که با # شروع می‌شوند)
            if line and not COMMENT_REGEX.match(line):
                # اگه خط با http شروع بشه، لینک هست
                if line.startswith('http'):
                    sources.append(line)
    
    return sources

# ========== اسکرپ پروکسی از لینک‌ها ==========
def scrape_proxies_from_url(url, proxy_type):
    """گرفتن پروکسی از یک لینک"""
    global http_proxies, socks4_proxies, socks5_proxies
    
    try:
        print(f"[+] Scraping {proxy_type} from: {url[:50]}...")
        
        headers = {'User-Agent': USER_AGENT}
        response = requests.get(url, timeout=15, headers=headers)
        
        if response.status_code == 200:
            # پیدا کردن همه پروکسی‌ها در متن
            proxies = PROXY_REGEX.findall(response.text)
            
            with stats_lock:
                for proxy in proxies:
                    if proxy_type == 'http':
                        http_proxies.append(proxy)
                    elif proxy_type == 'socks4':
                        socks4_proxies.append(proxy)
                    elif proxy_type == 'socks5':
                        socks5_proxies.append(proxy)
                    
                    stats['scraped_proxies'] += 1
                    stats['total_proxies'] += 1
            
            print(f"    → Found {len(proxies)} proxies")
            return len(proxies)
        else:
            print(f"    → Failed (HTTP {response.status_code})")
            
    except Exception as e:
        print(f"    → Error: {str(e)[:30]}")
    
    return 0

def scrape_all_proxies():
    """اسکرپ پروکسی از همه لینک‌های config.ini"""
    cfg = read_config()
    if not cfg:
        return False
    
    print("\n" + "="*60)
    print("SCRAPING PROXIES FROM CONFIG.INI SOURCES")
    print("="*60)
    
    # پاک کردن لیست‌های قبلی
    http_proxies.clear()
    socks4_proxies.clear()
    socks5_proxies.clear()
    
    # گرفتن لینک‌ها از هر بخش
    http_sources = get_sources_from_config(cfg, "HTTP")
    socks4_sources = get_sources_from_config(cfg, "SOCKS4")
    socks5_sources = get_sources_from_config(cfg, "SOCKS5")
    
    print(f"\n[+] HTTP Sources: {len(http_sources)}")
    print(f"[+] SOCKS4 Sources: {len(socks4_sources)}")
    print(f"[+] SOCKS5 Sources: {len(socks5_sources)}")
    
    # اسکرپ HTTP
    print("\n" + "-"*40)
    print("SCRAPING HTTP PROXIES")
    print("-"*40)
    for url in http_sources:
        scrape_proxies_from_url(url, 'http')
        sleep(1)  # مکث بین درخواست‌ها
    
    # اسکرپ SOCKS4
    print("\n" + "-"*40)
    print("SCRAPING SOCKS4 PROXIES")
    print("-"*40)
    for url in socks4_sources:
        scrape_proxies_from_url(url, 'socks4')
        sleep(1)
    
    # اسکرپ SOCKS5
    print("\n" + "-"*40)
    print("SCRAPING SOCKS5 PROXIES")
    print("-"*40)
    for url in socks5_sources:
        scrape_proxies_from_url(url, 'socks5')
        sleep(1)
    
    # گزارش نهایی
    print("\n" + "="*60)
    print("SCRAPING COMPLETED")
    print("="*60)
    print(f"HTTP: {len(http_proxies)} proxies")
    print(f"SOCKS4: {len(socks4_proxies)} proxies")
    print(f"SOCKS5: {len(socks5_proxies)} proxies")
    print(f"TOTAL: {len(http_proxies) + len(socks4_proxies) + len(socks5_proxies)} proxies")
    print("="*60)
    
    return True

# ========== نمایش وضعیت ==========
def show_status():
    system('cls' if name == 'nt' else 'clear')
    
    with stats_lock:
        total = len(http_proxies) + len(socks4_proxies) + len(socks5_proxies)
        
        print("="*60)
        print("         TELEGRAM VIEW BOT - ACTIVE")
        print("="*60)
        print(f"Channel: {channel} | Post: {post}")
        print("-"*60)
        print(f"✅ VIEWS SENT: {stats['views_sent']}")
        print(f"🌐 Working Proxies: {stats['working_proxies']}")
        print(f"📦 Total Proxies: {total}")
        print(f"🔄 Scraped Proxies: {stats['scraped_proxies']}")
        print(f"❌ Failed Proxies: {stats['failed_proxies']}")
        print(f"⚠️  Token Errors: {stats['token_errors']}")
        print("-"*60)
        print(f"HTTP: {len(http_proxies)} | SOCKS4: {len(socks4_proxies)} | SOCKS5: {len(socks5_proxies)}")
        print("="*60)

# ========== تست پروکسی ==========
def test_proxy(proxy, proxy_type):
    """تست سریع پروکسی"""
    try:
        if proxy_type == 'http':
            proxies = {'http': f'http://{proxy}', 'https': f'http://{proxy}'}
        else:
            proxies = {'http': f'{proxy_type}://{proxy}', 'https': f'{proxy_type}://{proxy}'}
        
        r = requests.get(
            'https://t.me',
            proxies=proxies,
            timeout=5,
            headers={'User-Agent': USER_AGENT}
        )
        
        return r.status_code == 200
    except:
        return False

# ========== گرفتن توکن ==========
def get_token(proxy, proxy_type):
    try:
        session = requests.Session()
        
        if proxy_type == 'http':
            session.proxies = {'http': f'http://{proxy}', 'https': f'http://{proxy}'}
        else:
            session.proxies = {'http': f'{proxy_type}://{proxy}', 'https': f'{proxy_type}://{proxy}'}
        
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
            token_match = re.search(r'data-view="(\d+)"', response.text)
            if token_match:
                with stats_lock:
                    stats['working_proxies'] += 1
                return token_match.group(1), session
        
        with stats_lock:
            stats['failed_proxies'] += 1
        return None, None
        
    except:
        with stats_lock:
            stats['failed_proxies'] += 1
        return None, None

# ========== ارسال ویو ==========
def send_view(token, session):
    try:
        cookies = {
            'stel_dt': '-240',
            'stel_web_auth': 'https%3A%2F%2Fweb.telegram.org%2Fz%2F'
        }
        
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
            with stats_lock:
                stats['views_sent'] += 1
            return True
        else:
            with stats_lock:
                stats['token_errors'] += 1
            return False
            
    except:
        with stats_lock:
            stats['token_errors'] += 1
        return False

# ========== کنترل کننده ==========
def control(proxy, proxy_type):
    if not test_proxy(proxy, proxy_type):
        return
    
    token, session = get_token(proxy, proxy_type)
    
    if token and session:
        # هر پروکسی چند بار استفاده میشه
        for i in range(10):
            if send_view(token, session):
                # نمایش وضعیت هر 10 ویو
                if stats['views_sent'] % 10 == 0:
                    show_status()
            sleep(0.1)

# ========== شروع ویو زدن ==========
def start_view():
    global running
    
    while running:
        # اسکرپ پروکسی از لینک‌ها
        if not scrape_all_proxies():
            print("[-] Failed to scrape proxies!")
            sleep(10)
            continue
        
        total = len(http_proxies) + len(socks4_proxies) + len(socks5_proxies)
        
        if total == 0:
            print("[-] No proxies found! Retrying in 10 seconds...")
            sleep(10)
            continue
        
        # ترکیب همه پروکسی‌ها
        all_proxies = []
        for proxy in http_proxies[:500]:  # محدودیت برای جلوگیری از overload
            all_proxies.append((proxy, 'http'))
        for proxy in socks4_proxies[:500]:
            all_proxies.append((proxy, 'socks4'))
        for proxy in socks5_proxies[:500]:
            all_proxies.append((proxy, 'socks5'))
        
        print(f"\n[+] Starting {min(THREADS, len(all_proxies))} threads...")
        
        # اجرای همزمان
        threads = []
        for proxy, ptype in all_proxies[:THREADS]:
            thread = Thread(target=control, args=(proxy, ptype))
            thread.start()
            threads.append(thread)
            
            while active_count() > THREADS:
                sleep(0.1)
        
        # صبر برای اتمام
        for t in threads:
            t.join()
        
        print("\n[+] Cycle completed. Restarting in 5 seconds...")
        sleep(5)

# ========== مانیتور ویو ==========
def monitor_views():
    while running:
        try:
            r = requests.get(
                f'https://t.me/{channel}/{post}',
                params={'embed': '1', 'mode': 'tme'},
                headers={'User-Agent': USER_AGENT},
                timeout=10
            )
            
            if r.status_code == 200:
                views_match = re.search(r'<span class="tgme_widget_message_views">([^<]+)', r.text)
                if views_match:
                    views_text = views_match.group(1)
                    
                    if 'K' in views_text:
                        real_views = int(float(views_text.replace('K', '')) * 1000)
                    elif 'M' in views_text:
                        real_views = int(float(views_text.replace('M', '')) * 1000000)
                    else:
                        real_views = int(views_text.replace(',', ''))
                    
                    show_status()
                    
        except:
            pass
            
        sleep(3)

# ========== MAIN ==========
if __name__ == "__main__":
    system('cls' if name == 'nt' else 'clear')
    
    print("="*60)
    print("    TELEGRAM VIEW BOT - PROXY SCRAPER + VIEWER")
    print("="*60)
    print("\n[!] This bot scrapes proxies from links in config.ini")
    print("[!] Then uses them to send views\n")
    
    # گرفتن لینک
    url = input("Enter Telegram post URL: ").strip()
    
    try:
        if 't.me/' in url:
            parts = url.split('t.me/')[1].split('/')
            channel = parts[0]
            post = int(parts[1])
        else:
            channel, post = url.split('/')
            post = int(post)
    except:
        print("[-] Invalid URL!")
        print("    Use format: https://t.me/channel/123")
        sys.exit(1)
    
    print(f"\n[+] Target: {channel} - Post {post}")
    
    # شروع نخ‌ها
    print("\n[+] Starting threads...")
    Thread(target=start_view, daemon=True).start()
    Thread(target=monitor_views, daemon=True).start()
    
    # نمایش وضعیت اولیه
    show_status()
    
    # نگه داشتن برنامه
    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        print("\n\n[+] Stopping bot...")
        running = False
        
        # نمایش آمار نهایی
        with stats_lock:
            print("\n" + "="*60)
            print("FINAL STATISTICS:")
            print("="*60)
            print(f"✅ Views Sent: {stats['views_sent']}")
            print(f"🌐 Working Proxies: {stats['working_proxies']}")
            print(f"📦 Total Proxies: {len(http_proxies) + len(socks4_proxies) + len(socks5_proxies)}")
            print(f"🔄 Scraped Proxies: {stats['scraped_proxies']}")
            print(f"❌ Failed Proxies: {stats['failed_proxies']}")
            print(f"⚠️  Token Errors: {stats['token_errors']}")
            print("="*60)
