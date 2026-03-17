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

THREADS = 500
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36'
MAX_CONSECUTIVE_FAILURES = 3
VIEW_DELAY = 0.5

REGEX = compile(r"(?:^|\D)?(("+ r"(?:[1-9]|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"):" + (r"(?:\d|[1-9]\d{1,3}|[1-5]\d{4}|6[0-4]\d{3}"
                + r"|65[0-4]\d{2}|655[0-2]\d|6553[0-5])")
                + r")(?:\D|$)")

# Statistics variables
stats_lock = Lock()
start_time = time()
total_views_sent = 0
successful_views = 0
failed_views = 0
proxy_errors = 0
token_errors = 0
socks5_proxies_found = 0
socks5_proxies_used = 0
views_per_minute = deque(maxlen=60)
last_view_time = time()
current_view_rate = 0
total_scrap_cycles = 0
total_proxies_loaded = 0
active_proxies_count = 0
blocked_proxies = 0

errors = open('errors.txt', 'a+')
cfg = ConfigParser(interpolation=None)
cfg.read("config.ini", encoding="utf-8")

# فقط SOCKS5
try:
    socks5 = cfg["SOCKS5"]
except KeyError:
    print(' [ ERROR ] SOCKS5 section not found in config.ini!')
    print(' Please make sure your config.ini has [SOCKS5] section')
    sleep(3)
    exit()

socks5_proxies = []
proxy_queue = Queue()
channel, post, time_out, real_views = '', 0, 15, 0


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


def print_statistics():
    while True:
        sleep(1)
        system('cls' if name == 'nt' else 'clear')
        
        elapsed_time = time() - start_time
        elapsed_str = str(timedelta(seconds=int(elapsed_time)))
        
        success_rate = (successful_views / total_views_sent * 100) if total_views_sent > 0 else 0
        
        current_time = time()
        views_in_last_minute = sum(1 for t, _ in views_per_minute if current_time - t <= 60)
        
        print("=" * 60)
        print("              TELEGRAM VIEW BOT - SOCKS5 ONLY")
        print("=" * 60)
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
        print(f"    • Total Views Sent: {total_views_sent:,}")
        print(f"    • Successful Views: {successful_views:,}")
        print(f"    • Failed Views: {failed_views:,}")
        print(f"    • Success Rate: {success_rate:.1f}%")
        print(f"    • Proxy Errors: {proxy_errors:,}")
        print(f"    • Token Errors: {token_errors:,}")
        print()
        print(f" 🌐 PROXY STATISTICS")
        print(f"    • Scrap Cycles: {total_scrap_cycles}")
        print(f"    • Total Proxies Loaded: {total_proxies_loaded:,}")
        print(f"    • Active Proxies: {active_proxies_count}")
        print(f"    • Blocked Proxies: {blocked_proxies}")
        print(f"    • SOCKS5 Proxies Found: {socks5_proxies_found:,}")
        print(f"    • SOCKS5 Proxies Used: {socks5_proxies_used:,}")
        print()
        print(f" 🔧 SYSTEM STATISTICS")
        print(f"    • Active Threads: {active_count()}")
        print(f"    • Max Threads: {THREADS}")
        print(f"    • Queue Size: {proxy_queue.qsize()}")
        print(f"    • Timeout: {time_out}s")
        print(f"    • View Delay: {VIEW_DELAY}s")
        print()
        print("=" * 60)
        print("           Press Ctrl+C to stop the bot")
        print("=" * 60)


def scrap(sources):
    global socks5_proxies_found, total_proxies_loaded
    
    for source in sources:
        if source and source.strip():
            try:
                print(f" [*] Scraping: {source[:50]}...")
                response = requests.get(source.strip(), timeout=time_out)
                
                if tuple(REGEX.finditer(response.text)):
                    proxies_found = 0
                    for proxy in tuple(REGEX.finditer(response.text)):
                        socks5_proxies.append(proxy.group(1))
                        proxies_found += 1
                    
                    with stats_lock:
                        socks5_proxies_found += proxies_found
                        total_proxies_loaded += proxies_found
                    
                    print(f" [✓] Found {proxies_found} proxies from {source[:50]}...")
                else:
                    print(f" [✗] No proxies found in {source[:50]}...")
                    
            except Exception as e:
                errors.write(f'{e}\n')
                print(f" [✗] Error scraping {source[:50]}: {str(e)[:50]}")


def start_scrap():
    global total_scrap_cycles
    
    socks5_proxies.clear()
    
    sources = [s for s in socks5.get("Sources").splitlines() if s.strip()]
    print(f" [*] Starting scrap cycle with {len(sources)} sources...")
    
    thread = Thread(target=scrap, args=(sources,))
    thread.start()
    thread.join()
    
    with stats_lock:
        total_scrap_cycles += 1
    
    print(f" [✓] Scrap cycle complete. Total proxies: {len(socks5_proxies)}")


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
    global active_proxies_count, blocked_proxies, socks5_proxies_used
    
    while True:
        try:
            proxy = proxy_queue.get(timeout=5)
            
            with stats_lock:
                active_proxies_count += 1
            
            consecutive_failures = 0
            session = None
            current_token = None
            views_with_this_proxy = 0
            
            print(f" [✓] Started using proxy: {proxy}")
            
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
                    else:
                        consecutive_failures += 1
                        with stats_lock:
                            update_stats(success=False)
                            proxy_errors += 1
                    
                    sleep(VIEW_DELAY)
                    
                except Exception as e:
                    consecutive_failures += 1
                    sleep(1)
            
            with stats_lock:
                active_proxies_count -= 1
                blocked_proxies += 1
            print(f" [✗] Proxy blocked after {views_with_this_proxy} views: {proxy}")
            
        except:
            sleep(1)


def start_view():
    while True:
        print(" [*] Starting new scrap cycle...")
        start_scrap()
        
        for proxy in socks5_proxies:
            proxy_queue.put(proxy)
        
        print(f" [*] Added {len(socks5_proxies)} proxies to queue")
        
        if proxy_queue.qsize() == 0:
            print(" [*] No proxies in queue, waiting...")
            sleep(5)
            continue
        
        while active_count() - 3 < THREADS and proxy_queue.qsize() > 0:
            Thread(target=proxy_worker, daemon=True).start()
            sleep(0.1)
        
        sleep(2)


def check_views():
    global real_views

    while True:
        try:
            telegram_request = requests.get(
                f'https://t.me/{channel}/{post}',
                params={'embed': '1', 'mode': 'tme'},
                headers={
                    'referer': f'https://t.me/{channel}/{post}',
                    'user-agent': USER_AGENT
                })

            views = search('<span class="tgme_widget_message_views">([^<]+)', telegram_request.text)
            if views:
                real_views = views.group(1)

            sleep(2)
        except:
            pass


system('cls' if name == 'nt' else 'clear')

print("=" * 60)
print("         TELEGRAM VIEW BOT - SOCKS5 ONLY EDITION")
print("=" * 60)
print()
print(" Features:")
print(" • SOCKS5 proxies only")
print(" • Each working proxy sends views until blocked")
print(f" • Max {MAX_CONSECUTIVE_FAILURES} consecutive failures before discarding")
print(f" • {VIEW_DELAY}s delay between views")
print(" • Real-time statistics")
print("=" * 60)
print()
url = input(" Enter Telegram View Post URL ==> ").replace('https://t.me/', '')
if '/' in url:
    channel, post = url.split('/')
else:
    print(" [ ERROR ] Invalid URL format!")
    exit()
print()
print(" Starting bot with SOCKS5 proxies only...")
print("=" * 60)
sleep(2)

# Start threads
Thread(target=start_view, daemon=True).start()
Thread(target=check_views, daemon=True).start()
Thread(target=print_statistics, daemon=True).start()

try:
    while True:
        sleep(1)
except KeyboardInterrupt:
    system('cls' if name == 'nt' else 'clear')
    print("=" * 60)
    print("                    BOT STOPPED - FINAL STATISTICS")
    print("=" * 60)
    print()
    print(f" Total Runtime: {str(timedelta(seconds=int(time() - start_time)))}")
    print(f" Total Views Sent: {total_views_sent:,}")
    print(f" Successful Views: {successful_views:,}")
    print(f" Failed Views: {failed_views:,}")
    print(f" Success Rate: {(successful_views/total_views_sent*100) if total_views_sent > 0 else 0:.1f}%")
    print(f" Blocked Proxies: {blocked_proxies}")
    print()
    print(" Thank you for using Telegram View Bot!")
    print("=" * 60)
