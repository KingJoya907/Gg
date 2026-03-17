import os
try:
    import requests
    from time import sleep, time
    from configparser import ConfigParser
    from os import system, name
    from threading import Thread, active_count, Lock
    from re import search, compile
    from datetime import datetime, timedelta
    from collections import deque
    from queue import Queue
except:
    os.system('pip install requests')
    os.system('pip install configparser')

# ==================== تنظیمات ====================
THREADS = 500
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36'
MAX_CONSECUTIVE_FAILURES = 3
VIEW_DELAY = 1.0
time_out = 15
PROXY_TEST_TIMEOUT = 3
MAX_TESTERS = 50
MIN_WORKING_PROXIES = 5

# ==================== REGEX ====================
REGEX = compile(r"(?:^|\D)?(("+ r"(?:[1-9]|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"):" + (r"(?:\d|[1-9]\d{1,3}|[1-5]\d{4}|6[0-4]\d{3}"
                + r"|65[0-4]\d{2}|655[0-2]\d|6553[0-5])")
                + r")(?:\D|$)")

# ==================== متغیرهای آمار ====================
stats_lock = Lock()
start_time = time()
total_views_sent = 0
successful_views = 0
failed_views = 0
proxy_errors = 0
token_errors = 0
socks5_proxies_found = 0
socks5_proxies_used = 0
socks5_proxies_tested = 0
socks5_proxies_working = 0
views_per_minute = deque(maxlen=60)
last_view_time = time()
current_view_rate = 0
total_scrap_cycles = 0
total_proxies_loaded = 0
active_proxies_count = 0
blocked_proxies = 0

# ==================== خواندن config.ini ====================
errors = open('errors.txt', 'a+')
cfg = ConfigParser(interpolation=None)
cfg.read("config.ini", encoding="utf-8")

try:
    socks5 = cfg["SOCKS5"]
except KeyError:
    print(' [ ERROR ] config.ini not found or invalid!')
    sleep(3)
    exit()

socks5_proxies = []
working_proxies = Queue()
proxy_queue = Queue()
channel, post, real_views = '', 0, '0'


# ==================== توابع آمار ====================
def update_stats(success=True):
    global total_views_sent, successful_views, failed_views, last_view_time, current_view_rate
    
    with stats_lock:
        total_views_sent += 1
        if success:
            successful_views += 1
        else:
            failed_views += 1
        
        current_time = time()
        time_diff = current_time - last_view_time
        if time_diff > 0:
            instant_rate = 1 / time_diff
            current_view_rate = (current_view_rate * 0.7) + (instant_rate * 0.3)
        
        views_per_minute.append((current_time, 1))
        last_view_time = current_time


def format_number(num):
    return f"{num:,}"


def print_statistics():
    while True:
        sleep(1)
        system('cls' if name == 'nt' else 'clear')
        
        elapsed_time = time() - start_time
        elapsed_str = str(timedelta(seconds=int(elapsed_time)))
        
        success_rate = (successful_views / total_views_sent * 100) if total_views_sent > 0 else 0
        
        current_time = time()
        views_in_last_minute = sum(1 for t, _ in views_per_minute if current_time - t <= 60)
        
        test_percent = (socks5_proxies_tested / total_proxies_loaded * 100) if total_proxies_loaded > 0 else 0
        
        print("="*60)
        print(" 🚀 TELEGRAM VIEW BOT - HYBRID EDITION 🚀".center(60))
        print("="*60)
        print()
        print(f" 📊 TARGET INFORMATION")
        print(f"    • Channel: @{channel}")
        print(f"    • Post ID: {post}")
        print(f"    • Current Views: {real_views}")
        print()
        print(f" ⏱️  TIME STATISTICS")
        print(f"    • Started: {datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"    • Elapsed: {elapsed_str}")
        print(f"    • Current Rate: {current_view_rate:.1f} views/sec")
        print(f"    • Views/Minute: {views_in_last_minute}")
        print()
        print(f" 📈 VIEW STATISTICS")
        print(f"    • Total Views Sent: {format_number(total_views_sent)}")
        print(f"    • Successful Views: {format_number(successful_views)}")
        print(f"    • Failed Views: {format_number(failed_views)}")
        print(f"    • Success Rate: {success_rate:.1f}%")
        print()
        print(f" 🌐 PROXY STATISTICS")
        print(f"    • Scrap Cycles: {total_scrap_cycles}")
        print(f"    • Total Proxies Loaded: {format_number(total_proxies_loaded)}")
        print(f"    • Proxies Tested: {format_number(socks5_proxies_tested)} ({test_percent:.1f}%)")
        print(f"    • Working Proxies: {format_number(socks5_proxies_working)}")
        print(f"    • Active Proxies: {active_proxies_count}")
        print(f"    • Blocked Proxies: {blocked_proxies}")
        print(f"    • Proxy Errors: {proxy_errors}")
        print(f"    • Token Errors: {token_errors}")
        print()
        print(f" 🔧 SYSTEM STATISTICS")
        print(f"    • Active Threads: {active_count()}")
        print(f"    • Max Threads: {THREADS}")
        print()
        print("="*60)
        print("           Press Ctrl+C to stop the bot".center(60))
        print("="*60)


# ==================== توابع اصلی (از کد قدیمی) ====================
def scrap(sources):
    global socks5_proxies_found, total_proxies_loaded
    
    for source in sources:
        if source:
            try:
                response = requests.get(source, timeout=time_out)
                
                if tuple(REGEX.finditer(response.text)):
                    for proxy in tuple(REGEX.finditer(response.text)):
                        socks5_proxies.append(proxy.group(1))
                        socks5_proxies_found += 1
                        total_proxies_loaded += 1
            except Exception as e:
                errors.write(f'{e}\n')


def start_scrap():
    global total_scrap_cycles, socks5_proxies
    
    socks5_proxies = []
    sources = socks5.get("Sources").splitlines()
    
    thread = Thread(target=scrap, args=(sources,))
    thread.start()
    thread.join()
    
    total_scrap_cycles += 1
    print(f" [✓] Found {len(socks5_proxies)} proxies")
    return len(socks5_proxies) > 0


def get_token(proxy):
    try:
        session = requests.session()
        
        response = session.get(
            f'https://t.me/{channel}/{post}',
            params={'embed': '1', 'mode': 'tme'},
            headers={'referer': f'https://t.me/{channel}/{post}', 'user-agent': USER_AGENT},
            proxies={'http': f'socks5://{proxy}', 'https': f'socks5://{proxy}'},
            timeout=time_out)
        
        token = search('data-view="([^"]+)', response.text)
        if token:
            return token.group(1), session
        return None, None
    except:
        return None, None


def send_view(token, session, proxy):
    try:
        cookies_dict = session.cookies.get_dict()
        
        response = session.get(
            'https://t.me/v/',
            params={'views': str(token)},
            cookies={'stel_dt': '-240', 'stel_web_auth': 'https%3A%2F%2Fweb.telegram.org%2Fz%2F',
                    'stel_ssid': cookies_dict.get('stel_ssid'), 'stel_on': cookies_dict.get('stel_on')},
            headers={'referer': f'https://t.me/{channel}/{post}?embed=1&mode=tme',
                    'user-agent': USER_AGENT, 'x-requested-with': 'XMLHttpRequest'},
            proxies={'http': f'socks5://{proxy}', 'https': f'socks5://{proxy}'},
            timeout=time_out)
        
        return response.status_code == 200 and response.text == 'true'
    except:
        return False


def proxy_worker():
    global active_proxies_count, blocked_proxies, socks5_proxies_used
    
    while True:
        try:
            if working_proxies.empty():
                sleep(1)
                continue
            
            proxy = working_proxies.get()
            
            active_proxies_count += 1
            consecutive_failures = 0
            views_with_this_proxy = 0
            
            while consecutive_failures < MAX_CONSECUTIVE_FAILURES:
                token, session = get_token(proxy)
                
                if not token:
                    consecutive_failures += 1
                    sleep(1)
                    continue
                
                success = send_view(token, session, proxy)
                
                if success:
                    consecutive_failures = 0
                    views_with_this_proxy += 1
                    socks5_proxies_used += 1
                    update_stats(success=True)
                else:
                    consecutive_failures += 1
                    update_stats(success=False)
                
                sleep(VIEW_DELAY)
            
            active_proxies_count -= 1
            blocked_proxies += 1
            
        except Exception as e:
            sleep(1)


def test_proxy(proxy):
    try:
        session = requests.session()
        response = session.get(
            'http://httpbin.org/ip',
            proxies={'http': f'socks5://{proxy}', 'https': f'socks5://{proxy}'},
            timeout=PROXY_TEST_TIMEOUT)
        return response.status_code == 200
    except:
        return False


def proxy_tester():
    global socks5_proxies_tested, socks5_proxies_working
    
    while True:
        try:
            if proxy_queue.empty():
                sleep(0.5)
                continue
            
            proxy = proxy_queue.get()
            socks5_proxies_tested += 1
            
            if test_proxy(proxy):
                working_proxies.put(proxy)
                socks5_proxies_working += 1
        except:
            sleep(1)


def start_view():
    while True:
        print("\n" + "="*60)
        print(" 🚀 Starting New Cycle...")
        print("="*60)
        
        # اسکرپ پروکسی
        if start_scrap():
            for proxy in socks5_proxies:
                proxy_queue.put(proxy)
            print(f" [✓] Added {len(socks5_proxies)} proxies to test queue")
        
        # ایجاد تسترها
        for i in range(MAX_TESTERS):
            Thread(target=proxy_tester, daemon=True).start()
        
        # منتظر ماندن برای پروکسی‌های کارآمد
        wait_time = 0
        while working_proxies.qsize() < MIN_WORKING_PROXIES and wait_time < 30:
            sleep(2)
            wait_time += 2
            print(f" [*] Waiting for working proxies... ({working_proxies.qsize()}/{MIN_WORKING_PROXIES})")
        
        # شروع workerها
        if working_proxies.qsize() >= MIN_WORKING_PROXIES:
            workers_count = min(THREADS, working_proxies.qsize())
            print(f" [🚀] Starting {workers_count} workers...")
            
            for i in range(workers_count):
                Thread(target=proxy_worker, daemon=True).start()
            
            print(f" [✓] Workers started!")
        
        sleep(10)


def check_views():
    global real_views
    
    while True:
        try:
            response = requests.get(
                f'https://t.me/{channel}/{post}',
                params={'embed': '1', 'mode': 'tme'},
                headers={'referer': f'https://t.me/{channel}/{post}', 'user-agent': USER_AGENT})
            
            views = search('<span class="tgme_widget_message_views">([^<]+)', response.text)
            if views:
                real_views = views.group(1)
            
            sleep(2)
        except:
            pass


# ==================== اجرا ====================
system('cls' if name == 'nt' else 'clear')

print("\n" + "="*60)
print(" 🚀 TELEGRAM VIEW BOT - HYBRID EDITION 🚀".center(60))
print("="*60)
print()

url = input(" Enter Telegram View Post URL ==> ").replace('https://t.me/', '').strip()
if '/' in url:
    channel, post = url.split('/')
    print(f"\n [✓] Channel: @{channel}")
    print(f" [✓] Post ID: {post}")
else:
    print("\n [❌] Invalid URL!")
    exit()

print("\n" + "="*60)
print(" 🚀 Starting Bot...")
print("="*60 + "\n")

Thread(target=start_view, daemon=True).start()
Thread(target=check_views, daemon=True).start()
Thread(target=print_statistics, daemon=True).start()

try:
    while True:
        sleep(1)
except KeyboardInterrupt:
    print("\n" + "="*60)
    print(" 📊 FINAL STATISTICS".center(60))
    print("="*60)
    print(f"\n Total Views Sent: {format_number(total_views_sent)}")
    print(f" Successful Views: {format_number(successful_views)}")
    print(f" Working Proxies: {socks5_proxies_working}")
    print("\n" + "="*60)
