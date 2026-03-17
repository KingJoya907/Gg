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
    print(f" [✓] Libraries installed: {e}")

# ==================== تنظیمات بهینه برای حداکثر سرعت ====================
THREADS = 500  # افزایش به 500 برای ویو زدن سریع‌تر
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
MAX_CONSECUTIVE_FAILURES = 3
VIEW_DELAY = 1.0  # کاهش به 1 ثانیه برای ویو سریع‌تر
time_out = 15
PROXY_TEST_TIMEOUT = 2  # کاهش به 2 ثانیه برای تست سریع
MAX_TESTERS = 200  # افزایش به 200 تستر همزمان
MIN_WORKING_PROXIES = 10  # شروع ویو با 10 پروکسی کارآمد
BATCH_SIZE = 100  # تست گروهی 100 تایی
DEBUG_MODE = True  # فعال برای دیدن جزئیات

# ==================== REGEX برای استخراج پروکسی ====================
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
testing_complete = False

# ==================== خواندن config.ini ====================
errors = open('errors.txt', 'a+')
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
    https://raw.githubusercontent.com/vakhov/fresh-proxy-list/main/socks5.txt
    https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS5_RAW.txt
    https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt
""")
    print(" [✓] Default config.ini created successfully!")
    print("="*60 + "\n")

cfg.read(config_path, encoding="utf-8")

try:
    socks5 = cfg["SOCKS5"]
    sources_count = len([s for s in socks5.get("Sources").splitlines() if s.strip()])
    print(f" [✓] SOCKS5 section loaded with {sources_count} sources")
except KeyError:
    print('\n' + "="*60)
    print(' [❌] ERROR: SOCKS5 section not found in config.ini!')
    print(' Please make sure your config.ini has [SOCKS5] section')
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
    """فرمت اعداد با کاما"""
    return f"{num:,}"


def print_statistics():
    global testing_complete, socks5_proxies_tested, total_proxies_loaded
    
    while True:
        sleep(1)
        system('cls' if name == 'nt' else 'clear')
        
        elapsed_time = time() - start_time
        elapsed_str = str(timedelta(seconds=int(elapsed_time)))
        
        success_rate = (successful_views / total_views_sent * 100) if total_views_sent > 0 else 0
        
        current_time = time()
        views_in_last_minute = sum(1 for t, _ in views_per_minute if current_time - t <= 60)
        
        # محاسبه درصد پیشرفت تست
        test_percent = (socks5_proxies_tested / total_proxies_loaded * 100) if total_proxies_loaded > 0 else 0
        test_speed = socks5_proxies_tested / (elapsed_time + 0.1)
        remaining = total_proxies_loaded - socks5_proxies_tested
        eta = remaining / test_speed if test_speed > 0 else 0
        
        # بررسی تکمیل تست
        if socks5_proxies_tested >= total_proxies_loaded and total_proxies_loaded > 0:
            testing_complete = True
        
        print("="*60)
        print(" 🚀 TELEGRAM VIEW BOT - ULTRA FAST EDITION 🚀".center(60))
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
        print(f"    • Working Queue: {working_proxies.qsize()}")
        print(f"    • Test Queue: {proxy_queue.qsize()}")
        print(f"    • Test Speed: {test_speed:.1f} proxies/sec")
        print(f"    • ETA: {str(timedelta(seconds=int(eta)))}")
        print(f"    • Testing Status: {'✅ COMPLETE' if testing_complete else '⚡ IN PROGRESS'}")
        print()
        print(f" 🔧 SYSTEM STATISTICS")
        print(f"    • Active Threads: {active_count()}")
        print(f"    • Max Threads: {THREADS}")
        print(f"    • Active Testers: {active_count() - (active_proxies_count + 3)}")
        print(f"    • Timeout: {time_out}s")
        print(f"    • View Delay: {VIEW_DELAY}s")
        print(f"    • Batch Size: {BATCH_SIZE}")
        print()
        print("="*60)
        print("           Press Ctrl+C to stop the bot".center(60))
        print("="*60)


# ==================== تست پروکسی با سرعت بالا ====================
def test_proxy_batch(proxies):
    """تست گروهی پروکسی‌ها با سرعت بالا"""
    working = []
    
    for proxy in proxies:
        try:
            start_test = time()
            session = requests.session()
            response = session.get(
                'http://httpbin.org/ip',
                proxies={
                    'http': f'socks5://{proxy}',
                    'https': f'socks5://{proxy}'
                },
                timeout=PROXY_TEST_TIMEOUT)
            
            if response.status_code == 200:
                working.append(proxy)
                response_time = int((time() - start_test) * 1000)
                if DEBUG_MODE and len(working) % 10 == 0:
                    print(f" [⚡] Found working proxy: {proxy} ({response_time}ms)")
        except:
            pass
    
    return working


def proxy_tester_ultra():
    """تستر فوق سریع با قابلیت پردازش گروهی"""
    global socks5_proxies_tested, socks5_proxies_working
    
    batch = []
    
    while True:
        try:
            # جمع‌آوری سریع یک دسته پروکسی
            while len(batch) < BATCH_SIZE and not proxy_queue.empty():
                try:
                    proxy = proxy_queue.get_nowait()
                    batch.append(proxy)
                except:
                    break
            
            if batch:
                # تست گروهی با سرعت بالا
                working = test_proxy_batch(batch)
                
                with stats_lock:
                    socks5_proxies_tested += len(batch)
                    for proxy in working:
                        working_proxies.put(proxy)
                        socks5_proxies_working += 1
                    
                    if DEBUG_MODE and len(working) > 0:
                        print(f" [📊] Batch: {len(working)}/{len(batch)} working | " +
                              f"Total: {socks5_proxies_working}/{socks5_proxies_tested}")
                
                batch.clear()
            else:
                sleep(0.1)  # کاهش زمان انتظار
                
        except Exception as e:
            if DEBUG_MODE:
                print(f" [⚠️] Tester error: {e}")
            sleep(0.5)


# ==================== توابع اسکرپ پروکسی ====================
def scrap(sources):
    global socks5_proxies_found, total_proxies_loaded
    
    for source in sources:
        if source and source.strip():
            try:
                if DEBUG_MODE:
                    print(f" [*] Scraping: {source[:60]}...")
                
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
                        
                        print(f" [✓] Found {proxies_found} proxies from {source[:40]}...")
                    else:
                        print(f" [✗] No proxies found in {source[:40]}...")
                else:
                    print(f" [✗] HTTP {response.status_code} from {source[:40]}...")
                    
            except Exception as e:
                errors.write(f'{e}\n')
                print(f" [✗] Error scraping {source[:40]}: {str(e)[:30]}")


def start_scrap():
    global total_scrap_cycles
    
    socks5_proxies.clear()
    
    sources = [s for s in socks5.get("Sources").splitlines() if s.strip()]
    print(f"\n [*] Starting scrap cycle with {len(sources)} sources...")
    
    # اسکرپ همزمان برای سرعت بیشتر
    threads = []
    chunk_size = max(1, len(sources) // 5)
    for i in range(0, len(sources), chunk_size):
        chunk = sources[i:i+chunk_size]
        thread = Thread(target=scrap, args=(chunk,))
        thread.start()
        threads.append(thread)
    
    for t in threads:
        t.join()
    
    with stats_lock:
        total_scrap_cycles += 1
    
    print(f" [✓] Scrap cycle complete. Total proxies: {len(socks5_proxies)}")
    print(f" [✓] Proxies found: {socks5_proxies_found}")


# ==================== توابع اصلی تلگرام ====================
def get_token(proxy):
    try:
        session = requests.session()
        
        response = session.get(
            f'https://t.me/{channel}/{post}',
            params={'embed': '1', 'mode': 'tme'},
            headers={
                'referer': f'https://t.me/{channel}/{post}',
                'user-agent': USER_AGENT
            },
            proxies={
                'http': f'socks5://{proxy}',
                'https': f'socks5://{proxy}'
            },
            timeout=time_out)

        token = search('data-view="([^"]+)', response.text)
        
        if token:
            return token.group(1), session
        return None, None

    except Exception as e:
        return None, None


def send_view(token, session, proxy):
    try:
        cookies_dict = session.cookies.get_dict() if session else {}

        response = session.get(
            'https://t.me/v/',
            params={'views': str(token)},
            cookies={
                'stel_dt': '-240',
                'stel_web_auth': 'https%3A%2F%2Fweb.telegram.org%2Fz%2F',
                'stel_ssid': cookies_dict.get('stel_ssid', None),
                'stel_on': cookies_dict.get('stel_on', None)
            },
            headers={
                'referer': f'https://t.me/{channel}/{post}?embed=1&mode=tme',
                'user-agent': USER_AGENT,
                'x-requested-with': 'XMLHttpRequest'
            },
            proxies={
                'http': f'socks5://{proxy}',
                'https': f'socks5://{proxy}'
            },
            timeout=time_out)

        return response.status_code == 200 and response.text == 'true'

    except:
        return False


def proxy_worker():
    """کارگر ویو زدن با پروکسی‌های کارآمد"""
    global active_proxies_count, blocked_proxies, socks5_proxies_used
    
    while True:
        try:
            proxy = working_proxies.get(timeout=5)
            
            with stats_lock:
                active_proxies_count += 1
            
            consecutive_failures = 0
            session = None
            current_token = None
            views_with_this_proxy = 0
            
            print(f" [🚀] Worker started with proxy: {proxy}")
            
            while consecutive_failures < MAX_CONSECUTIVE_FAILURES:
                try:
                    if not current_token or not session:
                        token_result, new_session = get_token(proxy)
                        
                        if token_result and new_session:
                            current_token = token_result
                            session = new_session
                            consecutive_failures = 0
                        else:
                            consecutive_failures += 1
                            sleep(1)
                            continue
                    
                    success = send_view(current_token, session, proxy)
                    
                    if success:
                        consecutive_failures = 0
                        views_with_this_proxy += 1
                        with stats_lock:
                            update_stats(success=True)
                            socks5_proxies_used += 1
                        
                        if views_with_this_proxy % 50 == 0:
                            print(f" [✓] {views_with_this_proxy} views sent with {proxy}")
                    else:
                        consecutive_failures += 1
                        with stats_lock:
                            update_stats(success=False)
                    
                    sleep(VIEW_DELAY)
                    
                except Exception as e:
                    consecutive_failures += 1
                    sleep(1)
            
            with stats_lock:
                active_proxies_count -= 1
                blocked_proxies += 1
            print(f" [⛔] Proxy blocked after {views_with_this_proxy} views: {proxy}")
            
        except:
            sleep(1)


def start_ultra_bot():
    """مدیریت اصلی بات با حداکثر سرعت"""
    global testing_complete
    
    while True:
        print("\n" + "="*60)
        print(" 🚀 Starting Ultra Fast Proxy Testing...")
        print("="*60)
        
        start_scrap()
        
        # اضافه کردن همه پروکسی‌ها به صف تست
        for proxy in socks5_proxies:
            proxy_queue.put(proxy)
        
        print(f" [✓] Added {len(socks5_proxies)} proxies to test queue")
        print(f" [✓] Starting {MAX_TESTERS} ultra fast testers...")
        
        # ایجاد تسترهای فوق سریع
        for i in range(MAX_TESTERS):
            Thread(target=proxy_tester_ultra, daemon=True).start()
            if i % 50 == 0:
                sleep(0.1)
        
        print(f" [✓] {MAX_TESTERS} testers are now running")
        
        # منتظر ماندن برای جمع شدن پروکسی‌های کارآمد
        last_working = 0
        start_wait = time()
        
        while proxy_queue.qsize() > 0 or working_proxies.qsize() < MIN_WORKING_PROXIES:
            elapsed = int(time() - start_wait)
            
            if working_proxies.qsize() > last_working:
                speed = socks5_proxies_tested / (elapsed + 1)
                remaining = proxy_queue.qsize()
                eta = remaining / speed if speed > 0 else 0
                
                print(f" [⚡] Progress: {socks5_proxies_tested}/{total_proxies_loaded} tested, " +
                      f"Working: {socks5_proxies_working}, " +
                      f"Speed: {speed:.0f}/sec, " +
                      f"ETA: {str(timedelta(seconds=int(eta)))}")
                
                last_working = working_proxies.qsize()
            
            sleep(2)
        
        print(f"\n [🎯] Target reached! {working_proxies.qsize()} working proxies ready")
        
        # ایجاد workerهای ویو زن
        if working_proxies.qsize() > 0:
            worker_count = min(THREADS, working_proxies.qsize())
            print(f" [🚀] Starting {worker_count} view workers...")
            
            for i in range(worker_count):
                Thread(target=proxy_worker, daemon=True).start()
                sleep(0.05)
            
            print(f" [✓] {worker_count} workers are now sending views!")
            print(f" [✓] Estimated rate: {worker_count/VIEW_DELAY:.0f} views/sec")
        
        # ادامه تست در پس‌زمینه
        while proxy_queue.qsize() > 0:
            sleep(5)
            print(f" [*] Background testing: {proxy_queue.qsize()} proxies remaining")
        
        print(" [✓] All proxies tested! Continuing with current workers...")
        sleep(10)


def check_views():
    """بررسی ویوهای واقعی پست"""
    global real_views

    while True:
        try:
            response = requests.get(
                f'https://t.me/{channel}/{post}',
                params={'embed': '1', 'mode': 'tme'},
                headers={
                    'referer': f'https://t.me/{channel}/{post}',
                    'user-agent': USER_AGENT
                },
                timeout=10)

            views = search('<span class="tgme_widget_message_views">([^<]+)', response.text)
            if views:
                real_views = views.group(1)

            sleep(2)
        except:
            pass


# ==================== اجرای اصلی ====================
system('cls' if name == 'nt' else 'clear')

print("\n" + "="*60)
print(" 🚀🚀🚀 TELEGRAM VIEW BOT - ULTRA FAST EDITION 🚀🚀🚀".center(60))
print("="*60)
print()
print(" ⚡ Features:")
print("    • Ultra fast proxy testing (200 testers)")
print("    • Batch testing (100 proxies at once)")
print("    • Real-time statistics with ETA")
print("    • Automatic view sending with working proxies")
print("    • Background testing while sending views")
print()
print(f" ⚙️  Settings:")
print(f"    • Proxy test timeout: {PROXY_TEST_TIMEOUT}s")
print(f"    • View delay: {VIEW_DELAY}s")
print(f"    • Max threads: {THREADS}")
print(f"    • Min working proxies to start: {MIN_WORKING_PROXIES}")
print()
print("="*60)
print()

url = input(" Enter Telegram View Post URL ==> ").replace('https://t.me/', '').strip()
if '/' in url:
    channel, post = url.split('/')
    print(f"\n [✓] Channel: @{channel}")
    print(f" [✓] Post ID: {post}")
else:
    print("\n [❌] ERROR: Invalid URL format!")
    print(" Example: https://t.me/channel/123")
    exit()

print("\n" + "="*60)
print(" 🚀 Starting Ultra Fast Telegram View Bot...")
print("="*60 + "\n")
sleep(2)

# شروع threadهای اصلی
Thread(target=start_ultra_bot, daemon=True).start()
Thread(target=check_views, daemon=True).start()
Thread(target=print_statistics, daemon=True).start()

# نگه داشتن برنامه اصلی
try:
    while True:
        sleep(1)
except KeyboardInterrupt:
    system('cls' if name == 'nt' else 'clear')
    print("\n" + "="*60)
    print(" 📊 FINAL STATISTICS".center(60))
    print("="*60)
    print()
    print(f" Total Runtime: {str(timedelta(seconds=int(time() - start_time)))}")
    print(f" Total Views Sent: {format_number(total_views_sent)}")
    print(f" Successful Views: {format_number(successful_views)}")
    print(f" Failed Views: {format_number(failed_views)}")
    success_rate = (successful_views / total_views_sent * 100) if total_views_sent > 0 else 0
    print(f" Success Rate: {success_rate:.1f}%")
    print(f" Working Proxies Found: {format_number(socks5_proxies_working)}")
    print(f" Proxies Tested: {format_number(socks5_proxies_tested)}/{format_number(total_proxies_loaded)}")
    print()
    print(" 👋 Thank you for using Ultra Fast Telegram View Bot!")
    print("="*60 + "\n")
