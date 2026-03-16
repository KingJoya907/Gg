#!/usr/bin/env python3
# Telegram View Bot - Ultra Fast Version with Live Counter (ENGLISH)
# BYPASS ALL LIMITS - MAX SPEED

import os
import sys
import re
import threading
from threading import Thread, Lock
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
THREADS = 5000           # Maximum threads
TIMEOUT = 3              # Low timeout for speed
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
PROXY_CHECK_TIMEOUT = 2  # Proxy check timeout

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

# Stats lock for thread safety
stats_lock = Lock()

stats = {
    'total_proxies': 0,
    'working_proxies': 0,
    'failed_proxies': 0,
    'token_errors': 0,
    'views_sent': 0,
    'start_time': time(),
    'last_views': 0,
    'last_time': time()
}

channel = ''
post = 0
running = True

# ========== LOAD CONFIG ==========
cfg = ConfigParser(interpolation=None)
if not cfg.read("config.ini"):
    print("[!] ERROR: config.ini not found!")
    print("[+] Creating default config.ini...")
    
    with open("config.ini", "w") as f:
        f.write("""[HTTP]
Sources = https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt
          https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt
          https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt

[SOCKS4]
Sources = https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt
          https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks4.txt
          https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt

[SOCKS5]
Sources = https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt
          https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt
          https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt
""")
    cfg.read("config.ini")

# ========== UTILITY FUNCTIONS ==========
def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def format_number(num):
    """Format numbers to readable format (1K, 1M, etc)"""
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.1f}K"
    else:
        return str(num)

def print_status():
    """Show real-time statistics"""
    with stats_lock:
        elapsed = int(time() - stats['start_time'])
        
        # Calculate current speed
        current_time = time()
        time_diff = current_time - stats['last_time']
        if time_diff >= 1:
            views_diff = stats['views_sent'] - stats['last_views']
            current_speed = views_diff / time_diff
            stats['last_views'] = stats['views_sent']
            stats['last_time'] = current_time
        else:
            current_speed = 0
        
        # Average speed
        avg_speed = stats['views_sent'] / (elapsed if elapsed > 0 else 1)
    
    clear_screen()
    
    # ASCII box for Termux compatibility
    print("=" * 60)
    print("         TELEGRAM VIEW BOT - ULTRA FAST")
    print("=" * 60)
    print(f"Channel: {channel:<30} | Post: {post}")
    print("-" * 60)
    print(f"✅ VIEWS SENT: {stats['views_sent']}")
    print(f"📊 Current Speed: {current_speed:.1f} views/sec")
    print(f"📈 Average Speed: {avg_speed:.1f} views/sec")
    print(f"🎯 Total Views: {format_number(stats['views_sent'])}")
    print("-" * 60)
    print(f"🌐 Working Proxies: {stats['working_proxies']}")
    print(f"📦 Total Proxies: {stats['total_proxies']}")
    print(f"❌ Failed Proxies: {stats['failed_proxies']}")
    print(f"⚠️  Token Errors: {stats['token_errors']}")
    print("-" * 60)
    print(f"⏱️  Uptime: {elapsed//3600:02d}:{(elapsed%3600)//60:02d}:{elapsed%60:02d}")
    print("=" * 60)
    print("Press Ctrl+C to stop")
    print("=" * 60, flush=True)

# ========== PROXY SCRAPER ==========
def scrape_proxies(proxy_type):
    """Fast proxy scraping from sources"""
    sources = cfg.get(proxy_type.upper(), "Sources", fallback="").splitlines()
    queue = proxy_queues[proxy_type]
    
    for source in sources:
        source = source.strip()
        if not source:
            continue
            
        try:
            session = requests.Session()
            response = session.get(
                source, 
                timeout=TIMEOUT,
                headers={'User-Agent': USER_AGENT}
            )
            
            if response.status_code == 200:
                matches = PROXY_REGEX.findall(response.text)
                for ip, port in matches:
                    if queue.qsize() < 9000:
                        proxy = f"{ip}:{port}"
                        queue.put(proxy)
                        with stats_lock:
                            stats['total_proxies'] += 1
                        
        except Exception:
            continue
            
        sleep(0.1)

def start_scrapers():
    """Start all proxy scrapers"""
    threads = []
    for pt in PROXY_TYPES:
        for i in range(3):
            t = Thread(target=scrape_proxies, args=(pt,), daemon=True)
            t.start()
            threads.append(t)
    return threads

# ========== PROXY CHECKER ==========
def check_proxy_quick(proxy, proxy_type):
    """Quick proxy check by connecting to Telegram"""
    try:
        if proxy_type == 'http':
            proxies = {'http': f'http://{proxy}', 'https': f'http://{proxy}'}
        else:
            proxies = {'http': f'{proxy_type}://{proxy}', 'https': f'{proxy_type}://{proxy}'}
        
        start = time()
        r = requests.get(
            'https://t.me',
            proxies=proxies,
            timeout=PROXY_CHECK_TIMEOUT,
            headers={'User-Agent': USER_AGENT}
        )
        
        if r.status_code == 200 and (time() - start) < 3:
            with stats_lock:
                stats['working_proxies'] += 1
            return True
            
    except:
        with stats_lock:
            stats['failed_proxies'] += 1
        
    return False

# ========== GET TOKEN ==========
def get_token_fast(proxy, proxy_type):
    """Get view token with maximum speed"""
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
                return token_match.group(1), session
                
    except:
        pass
        
    return None, None

# ========== SEND VIEW ==========
def send_view_fast(token, session):
    """Send view with maximum speed"""
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
            
    except:
        pass
        
    return False

# ========== WORKER ==========
def worker(proxy_type):
    """Main worker thread"""
    queue = proxy_queues[proxy_type]
    
    while running:
        try:
            proxy = queue.get(timeout=1)
            
            # Quick proxy check
            if not check_proxy_quick(proxy, proxy_type):
                queue.task_done()
                continue
            
            # Use each proxy multiple times
            for attempt in range(10):  # 10 attempts per proxy
                token, session = get_token_fast(proxy, proxy_type)
                
                if token and session:
                    if send_view_fast(token, session):
                        # View sent successfully
                        pass
                        
                    # Update display every 10 views
                    if stats['views_sent'] % 10 == 0:
                        print_status()
                else:
                    with stats_lock:
                        stats['token_errors'] += 1
                
                sleep(0.02)  # Small delay between attempts
                
            queue.task_done()
            
        except Empty:
            continue
        except Exception:
            continue

# ========== VIEW MONITOR ==========
def monitor_views():
    """Monitor real Telegram view count"""
    last_real_views = 0
    
    while running:
        try:
            r = requests.get(
                f'https://t.me/{channel}/{post}',
                params={'embed': '1', 'mode': 'tme'},
                headers={'User-Agent': USER_AGENT},
                timeout=TIMEOUT
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
                    
                    # Calculate added views
                    if last_real_views > 0 and real_views > last_real_views:
                        added = real_views - last_real_views
                        with stats_lock:
                            print(f"\n[+] {added} new views added to post! (Total: {real_views})")
                    
                    last_real_views = real_views
                    
        except:
            pass
            
        sleep(3)

# ========== MAIN ==========
def main():
    global channel, post, running
    
    clear_screen()
    
    print("=" * 50)
    print("   TELEGRAM VIEW BOT - ULTRA FAST v2.0")
    print("   Live View Counter - English Version")
    print("=" * 50)
    
    url = input("\n[?] Enter Telegram post URL: ").strip()
    
    try:
        if 't.me/' in url:
            parts = url.split('t.me/')[1].split('/')
            channel = parts[0]
            post = int(parts[1])
        else:
            channel, post = url.split('/')
            post = int(post)
    except:
        print("[!] Invalid URL!")
        return
    
    print(f"[+] Target: {channel} - Post {post}")
    print("[+] Starting system...")
    
    # Start scrapers
    scraper_threads = start_scrapers()
    
    # Wait for proxies
    print("[+] Collecting proxies...")
    for i in range(5):
        total_proxies = proxy_queues['http'].qsize() + proxy_queues['socks4'].qsize() + proxy_queues['socks5'].qsize()
        print(f"[{i+1}/5] {total_proxies} proxies collected")
        sleep(1)
    
    # Start workers
    worker_count = min(THREADS, 3000)
    print(f"[+] Starting {worker_count} worker threads...")
    
    for i in range(worker_count):
        pt = PROXY_TYPES[i % 3]
        t = Thread(target=worker, args=(pt,), daemon=True)
        t.start()
    
    # Start monitor
    monitor = Thread(target=monitor_views, daemon=True)
    monitor.start()
    
    print("[+] System activated! Sending views...")
    print("[+] Waiting for statistics...")
    print("[+] Press Ctrl+C to stop")
    
    # Update display every second
    try:
        while running:
            print_status()
            sleep(1)
    except KeyboardInterrupt:
        print("\n[!] Stopping system...")
        running = False
        
        # Show final statistics
        print("\n" + "=" * 50)
        print("FINAL STATISTICS:")
        print("=" * 50)
        print(f"✅ Total Views Sent: {stats['views_sent']}")
        print(f"📊 Average Speed: {stats['views_sent'] / (time() - stats['start_time']):.1f} views/sec")
        print(f"🌐 Working Proxies: {stats['working_proxies']}")
        print(f"⏱️  Total Time: {int(time() - stats['start_time'])} seconds")
        print("=" * 50)

if __name__ == "__main__":
    # Increase thread limit
    threading.stack_size(65536)
    
    # Disable warnings
    requests.packages.urllib3.disable_warnings()
    
    main()
