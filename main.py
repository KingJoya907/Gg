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
except Exception as e:
    os.system('pip install requests')
    os.system('pip install configparser')

# ==================== تنظیمات ====================
THREADS = 500
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
MAX_CONSECUTIVE_FAILURES = 5  # افزایش به 5
VIEW_DELAY = 1.0
time_out = 20  # افزایش به 20 ثانیه
PROXY_TEST_TIMEOUT = 3
MAX_TESTERS = 100
MIN_WORKING_PROXIES = 5
BATCH_SIZE = 50
DEBUG_MODE = True
VERBOSE_DEBUG = True  # دیباگ کامل

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
token_success = 0
token_failures = 0
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
workers_started = False

# ==================== خواندن config.ini ====================
errors = open('errors.txt', 'a+', encoding='utf-8')
cfg = ConfigParser(interpolation=None)

config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")
if not os.path.exists(config_path):
    print("\n" + "="*60)
    print(" [⚠️] config.ini not found! Creating default file...")
    print("="*60)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write("""[SOCKS5]
Sources = 
    https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/protocols/socks5/data.txt
    https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks5&timeout=4000&anonymity=elite
    https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks5.txt
    https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt
""")
    print(" [✓] Default config.ini created!")

cfg.read(config_path, encoding="utf-8")

try:
    socks5 = cfg["SOCKS5"]
    sources = [s for s in socks5.get("Sources").splitlines() if s.strip()]
    print(f" [✓] SOCKS5 loaded with {len(sources)} sources")
except KeyError:
    print('\n' + "="*60)
    print(' [❌] ERROR: SOCKS5 section not found!')
    print("="*60)
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
        if time_diff > 0 and time_diff < 10:
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
        token_success_rate = (token_success / (token_success + token_failures) * 100) if (token_success + token_failures) > 0 else 0
        
        current_time = time()
        views_in_last_minute = sum(1 for t, _ in views_per_minute if current_time - t <= 60)
        
        test_percent = (socks5_proxies_tested / total_proxies_loaded * 100) if total_proxies_loaded > 0 else 0
        test_speed = socks5_proxies_tested / (elapsed_time + 0.1)
        remaining = total_proxies_loaded - socks5_proxies_tested
        eta = remaining / test_speed if test_speed > 0 else 0
        
        print("="*60)
        print(" 🚀 TELEGRAM VIEW BOT - DEBUG MODE 🚀".center(60))
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
        print(f"    • Workers Started: {'✅' if workers_started else '❌'}")
        print()
        print(f" 🎫 TOKEN STATISTICS")
        print(f"    • Token Success: {token_success}")
        print(f"    • Token Failures: {token_failures}")
        print(f"    • Token Success Rate: {token_success_rate:.1f}%")
        print()
        print(f" 🌐 PROXY STATISTICS")
        print(f"    • Scrap Cycles: {total_scrap_cycles}")
        print(f"    • Total Proxies Loaded: {format_number(total_proxies_loaded)}")
        print(f"    • Proxies Tested: {format_number(socks5_proxies_tested)} ({test_percent:.1f}%)")
        print(f"    • Working Proxies: {format_number(socks5_proxies_working)}")
        print(f"    • Active Proxies: {active_proxies_count}")
        print(f"    • Working Queue: {working_proxies.qsize()}")
        print(f"    • Test Queue: {proxy_queue.qsize()}")
        print(f"    • Test Speed: {test_speed:.1f}/sec")
        print(f"    • ETA: {str(timedelta(seconds=int(eta)))}")
        print()
        print(f" 🔧 SYSTEM STATISTICS")
        print(f"    • Active Threads: {active_count()}")
        print(f"    • Max Threads: {THREADS}")
        print(f"    • Active Testers: {max(0, active_count() - (active_proxies_count + 3))}")
        print()
        print("="*60)
        print("           Press Ctrl+C to stop".center(60))
        print("="*60)


# ==================== توابع اسکرپ ====================
def scrap(sources):
    global socks5_proxies_found, total_proxies_loaded, socks5_proxies
    
    for source in sources:
        if source and source.strip():
            try:
                if DEBUG_MODE:
                    print(f" [*] Scraping: {source[:50]}...")
                
                response = requests.get(source.strip(), timeout=30)
                
                if response.status_code == 200:
                    matches = tuple(REGEX.finditer(response.text))
                    if matches:
                        proxies_found = 0
                        for proxy in matches:
                            proxy_str = proxy.group(1)
                            socks5_proxies.append(proxy_str)
                            proxies_found += 1
                        
                        with stats_lock:
                            socks5_proxies_found += proxies_found
                            total_proxies_loaded += proxies_found
                        
                        print(f" [✓] Found {proxies_found} proxies")
                    else:
                        print(f" [✗] No proxies found")
            except Exception as e:
                errors.write(f'{e}\n')


def start_scrap():
    global total_scrap_cycles, socks5_proxies
    
    socks5_proxies = []
    sources_list = [s for s in socks5.get("Sources").splitlines() if s.strip()]
    
    print(f"\n [*] Scraping {len(sources_list)} sources...")
    
    threads = []
    for source in sources_list:
        thread = Thread(target=scrap, args=([source],))
        thread.start()
        threads.append(thread)
    
    for t in threads:
        t.join()
    
    with stats_lock:
        total_scrap_cycles += 1
    
    print(f" [✓] Found {len(socks5_proxies)} total proxies")
    return len(socks5_proxies) > 0


# ==================== تست پروکسی ====================
def proxy_tester():
    global socks5_proxies_tested, socks5_proxies_working
    
    while True:
        try:
            if not proxy_queue.empty():
                proxy = proxy_queue.get(timeout=1)
                
                try:
                    session = requests.session()
                    response = session.get(
                        'http://httpbin.org/ip',
                        proxies={'http': f'socks5://{proxy}', 'https': f'socks5://{proxy}'},
                        timeout=PROXY_TEST_TIMEOUT)
                    
                    with stats_lock:
                        socks5_proxies_tested += 1
                    
                    if response.status_code == 200:
                        working_proxies.put(proxy)
                        with stats_lock:
                            socks5_proxies_working += 1
                        if DEBUG_MODE:
                            print(f" [✓] Working: {proxy}")
                except Exception as e:
                    with stats_lock:
                        socks5_proxies_tested += 1
            else:
                sleep(0.5)
        except:
            sleep(1)


# ==================== توابع تلگرام با دیباگ ====================
def get_token(proxy):
    global token_success, token_failures
    
    try:
        if VERBOSE_DEBUG:
            print(f"\n [🔍] Getting token from {proxy}")
        
        session = requests.session()
        
        url = f'https://t.me/{channel}/{post}'
        params = {'embed': '1', 'mode': 'tme'}
        headers = {'referer': f'https://t.me/{channel}/{post}', 'user-agent': USER_AGENT}
        proxies = {'http': f'socks5://{proxy}', 'https': f'socks5://{proxy}'}
        
        if VERBOSE_DEBUG:
            print(f" [*] URL: {url}")
            print(f" [*] Timeout: {time_out}s")
        
        response = session.get(url, params=params, headers=headers, proxies=proxies, timeout=time_out)
        
        if VERBOSE_DEBUG:
            print(f" [*] Response Status: {response.status_code}")
            print(f" [*] Response Length: {len(response.text)}")
        
        if response.status_code == 200:
            token = search('data-view="([^"]+)', response.text)
            
            if token:
                if VERBOSE_DEBUG:
                    print(f" [✓] Token found: {token.group(1)[:20]}...")
                with stats_lock:
                    token_success += 1
                return token.group(1), session
            else:
                if VERBOSE_DEBUG:
                    print(f" [✗] No token in response")
                    print(f" [*] First 200 chars: {response.text[:200]}")
                with stats_lock:
                    token_failures += 1
                return None, None
        else:
            if VERBOSE_DEBUG:
                print(f" [✗] HTTP Error: {response.status_code}")
            with stats_lock:
                token_failures += 1
            return None, None
            
    except requests.exceptions.ConnectTimeout:
        if VERBOSE_DEBUG:
            print(f" [✗] Connection Timeout")
        with stats_lock:
            token_failures += 1
        return None, None
    except requests.exceptions.ProxyError as e:
        if VERBOSE_DEBUG:
            print(f" [✗] Proxy Error: {e}")
        with stats_lock:
            token_failures += 1
        return None, None
    except Exception as e:
        if VERBOSE_DEBUG:
            print(f" [✗] Error: {e}")
        with stats_lock:
            token_failures += 1
        return None, None


def send_view(token, session, proxy):
    try:
        if VERBOSE_DEBUG:
            print(f" [*] Sending view with token: {token[:20]}...")
        
        cookies_dict = session.cookies.get_dict() if session else {}
        
        response = session.get(
            'https://t.me/v/',
            params={'views': str(token)},
            cookies={'stel_dt': '-240', 'stel_web_auth': 'https%3A%2F%2Fweb.telegram.org%2Fz%2F',
                    'stel_ssid': cookies_dict.get('stel_ssid'), 'stel_on': cookies_dict.get('stel_on')},
            headers={'referer': f'https://t.me/{channel}/{post}?embed=1&mode=tme',
                    'user-agent': USER_AGENT, 'x-requested-with': 'XMLHttpRequest'},
            proxies={'http': f'socks5://{proxy}', 'https': f'socks5://{proxy}'},
            timeout=time_out)

        if VERBOSE_DEBUG:
            print(f" [*] View Response: {response.status_code} - {response.text}")
        
        return response.status_code == 200 and response.text == 'true'
    except Exception as e:
        if VERBOSE_DEBUG:
            print(f" [✗] Send view error: {e}")
        return False


# ==================== تابع اصلی ویو زدن ====================
def view_worker():
    global active_proxies_count, blocked_proxies, socks5_proxies_used, workers_started
    
    workers_started = True
    worker_id = id(threading.current_thread())
    
    while True:
        try:
            proxy = working_proxies.get(timeout=5)
            
            with stats_lock:
                active_proxies_count += 1
            
            print(f"\n [🚀] Worker-{worker_id} started with proxy: {proxy}")
            print(f" [*] Target: @{channel}/{post}")
            
            consecutive_failures = 0
            session = None
            current_token = None
            views_with_this_proxy = 0
            
            while consecutive_failures < MAX_CONSECUTIVE_FAILURES:
                try:
                    if not current_token or not session:
                        token_result, new_session = get_token(proxy)
                        
                        if token_result and new_session:
                            current_token = token_result
                            session = new_session
                            consecutive_failures = 0
                            print(f" [✓] Worker-{worker_id}: Token received")
                        else:
                            consecutive_failures += 1
                            print(f" [✗] Worker-{worker_id}: Token failed ({consecutive_failures}/{MAX_CONSECUTIVE_FAILURES})")
                            sleep(1)
                            continue
                    
                    success = send_view(current_token, session, proxy)
                    
                    if success:
                        consecutive_failures = 0
                        views_with_this_proxy += 1
                        with stats_lock:
                            update_stats(success=True)
                            socks5_proxies_used += 1
                        
                        print(f" [✓] Worker-{worker_id}: View #{total_views_sent} sent!")
                    else:
                        consecutive_failures += 1
                        with stats_lock:
                            update_stats(success=False)
                        print(f" [✗] Worker-{worker_id}: View failed ({consecutive_failures}/{MAX_CONSECUTIVE_FAILURES})")
                    
                    sleep(VIEW_DELAY)
                    
                except Exception as e:
                    consecutive_failures += 1
                    print(f" [✗] Worker-{worker_id}: Error: {e}")
                    sleep(1)
            
            with stats_lock:
                active_proxies_count -= 1
                blocked_proxies += 1
            print(f" [⛔] Worker-{worker_id}: Proxy blocked after {views_with_this_proxy} views")
            
        except Exception as e:
            print(f" [⚠️] Worker-{worker_id}: Queue error: {e}")
            sleep(1)


# ==================== تابع مدیریت ====================
def start_bot():
    global workers_started
    
    while True:
        print("\n" + "="*60)
        print(" 🚀 Starting New Cycle...")
        print("="*60)
        
        if start_scrap():
            for proxy in socks5_proxies:
                proxy_queue.put(proxy)
            print(f" [✓] Added {len(socks5_proxies)} proxies to test queue")
        
        if active_count() < 50:
            print(f" [✓] Starting {MAX_TESTERS} testers...")
            for i in range(MAX_TESTERS):
                Thread(target=proxy_tester, daemon=True).start()
        
        if working_proxies.qsize() >= MIN_WORKING_PROXIES and not workers_started:
            workers_count = min(THREADS, working_proxies.qsize())
            print(f"\n [🚀] STARTING {workers_count} VIEW WORKERS!")
            
            for i in range(workers_count):
                Thread(target=view_worker, daemon=True).start()
                sleep(0.1)
            
            workers_started = True
            print(f" [✓] Workers started! Est. rate: {workers_count/VIEW_DELAY:.0f} views/sec")
        
        print(f"\n [📊] Status:")
        print(f"    • Tested: {socks5_proxies_tested}/{total_proxies_loaded}")
        print(f"    • Working: {socks5_proxies_working}")
        print(f"    • Active Workers: {active_proxies_count}")
        print(f"    • Views Sent: {total_views_sent}")
        
        sleep(10)


def check_views():
    global real_views
    while True:
        try:
            r = requests.get(f'https://t.me/{channel}/{post}', params={'embed': '1', 'mode': 'tme'}, timeout=10)
            views = search('<span class="tgme_widget_message_views">([^<]+)', r.text)
            if views:
                real_views = views.group(1)
            sleep(2)
        except:
            pass


# ==================== اجرا ====================
system('cls' if name == 'nt' else 'clear')

print("\n" + "="*60)
print(" 🚀 TELEGRAM VIEW BOT - DEBUG MODE 🚀".center(60))
print("="*60)
print()
url = input(" Enter URL: ").replace('https://t.me/', '').strip()
if '/' in url:
    channel, post = url.split('/')
    print(f"\n [✓] Channel: @{channel}")
    print(f" [✓] Post ID: {post}")
else:
    print("\n [❌] Invalid URL!")
    exit()

print("\n" + "="*60)
print(" 🚀 Starting with DEBUG MODE...")
print("="*60 + "\n")

Thread(target=start_bot, daemon=True).start()
Thread(target=check_views, daemon=True).start()
Thread(target=print_statistics, daemon=True).start()

try:
    while True:
        sleep(1)
except KeyboardInterrupt:
    print("\n" + "="*60)
    print(" 📊 FINAL STATISTICS".center(60))
    print("="*60)
    print(f"\n Views Sent: {format_number(total_views_sent)}")
    print(f" Token Success: {token_success}")
    print(f" Token Failures: {token_failures}")
    print(f" Success Rate: {(token_success/(token_success+token_failures)*100) if (token_success+token_failures)>0 else 0:.1f}%")
    print(f" Working Proxies: {socks5_proxies_working}")
    print("\n" + "="*60)
