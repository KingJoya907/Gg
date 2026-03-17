import os
try:
 import requests
 from time import sleep, time
 from configparser import ConfigParser
 from os import system, name
 from threading import Thread, active_count, Lock
 from re import search, compile
 from collections import deque
 from datetime import datetime
 import random
 import json
except:
 os.system('pip install requests')
 os.system('pip install configparser')
 os.system('pip install datetime')
# ==================== تنظیمات پیشرفته ====================
THREADS = 300  # کاهش برای رفتار طبیعی‌تر
PROXIES_TYPES = ('http', 'socks4', 'socks5')

# لیست User-Agentهای واقعی و متنوع
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 13; SM-S911B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

# ==================== REGEX ====================
REGEX = compile(r"(?:^|\D)?(("+ r"(?:[1-9]|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"):" + (r"(?:\d|[1-9]\d{1,3}|[1-5]\d{4}|6[0-4]\d{3}"
                + r"|65[0-4]\d{2}|655[0-2]\d|6553[0-5])")
                + r")(?:\D|$)")

# ==================== آمار حرفه‌ای ====================
stats_lock = Lock()
start_time = time()
stats = {
    'total_views_sent': 0,
    'successful_views': 0,
    'failed_views': 0,
    'proxy_errors': 0,
    'token_errors': 0,
    'http_proxies_found': 0,
    'socks4_proxies_found': 0,
    'socks5_proxies_found': 0,
    'http_proxies_used': 0,
    'socks4_proxies_used': 0,
    'socks5_proxies_used': 0,
    'active_threads': 0,
    'views_per_minute': deque(maxlen=60),
    'last_view_time': time(),
    'current_rate': 0.0,
    'total_scrap_cycles': 0,
    'total_proxies_loaded': 0
}

# ==================== خواندن config.ini ====================
errors = open('errors.txt', 'a+')
cfg = ConfigParser(interpolation=None)
cfg.read("config.ini", encoding="utf-8")

try:
 http, socks4, socks5 = cfg["HTTP"], cfg["SOCKS4"], cfg["SOCKS5"]
except KeyError:
 print(' [ ERROR ] config.ini not found or incomplete!')
 print(' Creating default config.ini...')
 with open('config.ini', 'w', encoding='utf-8') as f:
     f.write("""[HTTP]
Sources = 

[SOCKS4]
Sources = 

[SOCKS5]
Sources = 
    https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt
    https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks5.txt
""")
 sleep(3)
 exit()

http_proxies, socks4_proxies, socks5_proxies = [], [], []


# ==================== توابع آمار ====================
def update_stats(success=True, proxy_type=None):
    with stats_lock:
        stats['total_views_sent'] += 1
        if success:
            stats['successful_views'] += 1
        else:
            stats['failed_views'] += 1
        
        current_time = time()
        time_diff = current_time - stats['last_view_time']
        if time_diff > 0:
            instant_rate = 1 / time_diff
            stats['current_rate'] = (stats['current_rate'] * 0.7) + (instant_rate * 0.3)
        
        stats['views_per_minute'].append((current_time, 1))
        stats['last_view_time'] = current_time


def print_statistics():
    while True:
        sleep(1)
        system('cls' if name == 'nt' else 'clear')
        
        elapsed_time = time() - start_time
        elapsed_str = f"{int(elapsed_time//3600):02d}:{int((elapsed_time%3600)//60):02d}:{int(elapsed_time%60):02d}"
        
        with stats_lock:
            total = stats['total_views_sent']
            success = stats['successful_views']
            success_rate = (success / total * 100) if total > 0 else 0
            
            current_time = time()
            views_last_min = sum(1 for t, _ in stats['views_per_minute'] if current_time - t <= 60)
        
        print("="*70)
        print(" 🚀 TELEGRAM VIEW BOT - HUMANIZED EDITION 🚀".center(70))
        print("="*70)
        print(f"\n 📊 TARGET INFORMATION")
        print(f"    • Channel: @{channel}")
        print(f"    • Post ID: {post}")
        print(f"    • Current Views: {real_views}")
        print()
        print(f" ⏱️  TIME STATISTICS")
        print(f"    • Started: {datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"    • Elapsed: {elapsed_str}")
        print(f"    • Current Rate: {stats['current_rate']:.2f} views/sec")
        print(f"    • Views/Minute: {views_last_min}")
        print()
        print(f" 📈 VIEW STATISTICS")
        print(f"    • Total Views Sent: {stats['total_views_sent']:,}")
        print(f"    • Successful Views: {stats['successful_views']:,}")
        print(f"    • Failed Views: {stats['failed_views']:,}")
        print(f"    • Success Rate: {success_rate:.2f}%")
        print(f"    • Proxy Errors: {stats['proxy_errors']}")
        print(f"    • Token Errors: {stats['token_errors']}")
        print()
        print(f" 🌐 PROXY STATISTICS")
        print(f"    • HTTP Proxies: {stats['http_proxies_found']} (Used: {stats['http_proxies_used']})")
        print(f"    • SOCKS4 Proxies: {stats['socks4_proxies_found']} (Used: {stats['socks4_proxies_used']})")
        print(f"    • SOCKS5 Proxies: {stats['socks5_proxies_found']} (Used: {stats['socks5_proxies_used']})")
        print(f"    • Active Threads: {active_count()}")
        print(f"    • Max Threads: {THREADS}")
        print()
        print("="*70)
        print(" Press Ctrl+C to stop".center(70))
        print("="*70)


# ==================== توابع اصلی با رفتار انسانی ====================
def human_delay():
    """تأخیرهای تصادفی شبیه انسان"""
    return random.uniform(0.5, 2.0)


def get_random_user_agent():
    """انتخاب رندوم User-Agent"""
    return random.choice(USER_AGENTS)


def scrap(sources, _proxy_type):
    for source in sources:
        if source:
            try:
                # تأخیر بین درخواست‌ها شبیه انسان
                sleep(random.uniform(0.5, 1.5))
                
                response = requests.get(source, timeout=time_out, headers={
                    'User-Agent': get_random_user_agent()
                })
                
                if tuple(REGEX.finditer(response.text)):
                    found_count = 0
                    for proxy in tuple(REGEX.finditer(response.text)):
                        if _proxy_type == 'http':
                            http_proxies.append(proxy.group(1))
                            stats['http_proxies_found'] += 1
                        elif _proxy_type == 'socks4':
                            socks4_proxies.append(proxy.group(1))
                            stats['socks4_proxies_found'] += 1
                        elif _proxy_type == 'socks5':
                            socks5_proxies.append(proxy.group(1))
                            stats['socks5_proxies_found'] += 1
                        found_count += 1
                    
                    with stats_lock:
                        stats['total_proxies_loaded'] += found_count
                        
            except Exception as e:
                errors.write(f'{e}\n')


def start_scrap():
    threads = []
    for i in (http_proxies, socks4_proxies, socks5_proxies):
        i.clear()

    sources_list = [
        (http.get("Sources").splitlines() if http else [], 'http'),
        (socks4.get("Sources").splitlines() if socks4 else [], 'socks4'),
        (socks5.get("Sources").splitlines() if socks5 else [], 'socks5')
    ]

    for sources, proxy_type in sources_list:
        if sources and sources[0]:  # اگر منبع وجود داشت
            thread = Thread(target=scrap, args=(sources, proxy_type))
            threads.append(thread)
            thread.start()
            sleep(human_delay())  # تأخیر بین شروع threadها

    for t in threads:
        t.join()
    
    with stats_lock:
        stats['total_scrap_cycles'] += 1


def get_token(proxy, proxy_type):
    try:
        session = requests.session()
        
        # تأخیر تصادفی قبل از درخواست
        sleep(random.uniform(0.3, 1.0))
        
        response = session.get(
            f'https://t.me/{channel}/{post}',
            params={'embed': '1', 'mode': 'tme'},
            headers={
                'referer': f'https://t.me/{channel}/{post}',
                'user-agent': get_random_user_agent(),
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'accept-language': 'en-US,en;q=0.5',
                'accept-encoding': 'gzip, deflate, br',
                'connection': 'keep-alive',
            },
            proxies={
                'http': f'{proxy_type}://{proxy}',
                'https': f'{proxy_type}://{proxy}'
            },
            timeout=time_out)

        token = search('data-view="([^"]+)', response.text)
        if token:
            return token.group(1), session
        return 2  # AttributeError

    except AttributeError:
        return 2
    except requests.exceptions.RequestException:
        return 1
    except Exception as e:
        errors.write(f'{e}\n')
        return None


def send_view(token, session, proxy, proxy_type):
    try:
        # تأخیر تصادفی شبیه انسان
        sleep(random.uniform(0.2, 0.8))
        
        cookies_dict = session.cookies.get_dict()

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
                'user-agent': get_random_user_agent(),
                'x-requested-with': 'XMLHttpRequest',
                'accept': '*/*',
                'accept-language': 'en-US,en;q=0.5',
            },
            proxies={
                'http': f'{proxy_type}://{proxy}',
                'https': f'{proxy_type}://{proxy}'
            },
            timeout=time_out)

        return response.status_code == 200 and response.text == 'true'

    except requests.exceptions.RequestException:
        return 1
    except Exception:
        return False


def control(proxy, proxy_type):
    token_data = get_token(proxy, proxy_type)

    if token_data == 2:
        with stats_lock:
            stats['token_errors'] += 1
            update_stats(success=False, proxy_type=proxy_type)
    elif token_data == 1:
        with stats_lock:
            stats['proxy_errors'] += 1
            update_stats(success=False, proxy_type=proxy_type)
    elif token_data:
        success = send_view(token_data[0], token_data[1], proxy, proxy_type)
        if success:
            with stats_lock:
                update_stats(success=True, proxy_type=proxy_type)
                if proxy_type == 'http':
                    stats['http_proxies_used'] += 1
                elif proxy_type == 'socks4':
                    stats['socks4_proxies_used'] += 1
                elif proxy_type == 'socks5':
                    stats['socks5_proxies_used'] += 1
        else:
            with stats_lock:
                update_stats(success=False, proxy_type=proxy_type)


def start_view():
    c, threads = 0, []
    start_scrap()

    for proxy_list in [http_proxies, socks4_proxies, socks5_proxies]:
        for proxy in proxy_list:
            # تأخیر تصادفی بین شروع threadها
            sleep(random.uniform(0.01, 0.1))
            
            thread = Thread(target=control, args=(proxy, PROXIES_TYPES[c]))
            threads.append(thread)

            while active_count() > THREADS:
                sleep(0.1)

            thread.start()

        c += 1
        # تأخیر طولانی‌تر بین نوع‌های مختلف پروکسی
        sleep(random.uniform(3, 5))

    # منتظر موندن با رفتار انسانی
    for t in threads:
        t.join(timeout=5)
    
    # تأخیر قبل از شروع دوباره
    sleep(random.uniform(5, 10))
    start_view()


def check_views():
    global real_views
    last_known = "0"

    while True:
        try:
            # درخواست با User-Agent متغیر
            response = requests.get(
                f'https://t.me/{channel}/{post}',
                params={'embed': '1', 'mode': 'tme'},
                headers={
                    'referer': f'https://t.me/{channel}/{post}',
                    'user-agent': get_random_user_agent()
                })

            views = search('<span class="tgme_widget_message_views">([^<]+)', response.text)
            if views:
                new_views = views.group(1)
                if new_views != last_known:
                    print(f"\n [🎯] REAL VIEWS UPDATED: {last_known} → {new_views}")
                    last_known = new_views
                real_views = new_views

            # تأخیر متغیر شبیه انسان
            sleep(random.uniform(5, 10))

        except:
            sleep(5)


# ==================== شروع برنامه ====================
system('cls' if name == 'nt' else 'clear')

print("="*70)
print(" 🚀 TELEGRAM VIEW BOT - HUMANIZED EDITION 🚀".center(70))
print("="*70)
print("\n ویژگی‌های انسانی:")
print(" ✓ User-Agentهای متغیر و واقعی")
print(" ✓ تأخیرهای تصادفی شبیه انسان")
print(" ✓ آمار حرفه‌ای لحظه‌ای")
print(" ✓ تشخیص ویوهای واقعی")
print(" ✓ مدیریت هوشمند threadها")
print("="*70)

channel, post = input("\n Telegram View Post URL: ").replace('https://t.me/', '').split('/')

print(f"\n [✓] Target: @{channel}/{post}")
print(" [✓] Starting bot with human-like behavior...\n")

# شروع threadها
Thread(target=start_view, daemon=True).start()
Thread(target=check_views, daemon=True).start()
Thread(target=print_statistics, daemon=True).start()

try:
    while True:
        sleep(1)
except KeyboardInterrupt:
    print("\n\n" + "="*70)
    print(" 📊 FINAL STATISTICS".center(70))
    print("="*70)
    print(f"\n Total Views Sent: {stats['total_views_sent']:,}")
    print(f" Successful Views: {stats['successful_views']:,}")
    print(f" Success Rate: {(stats['successful_views']/stats['total_views_sent']*100) if stats['total_views_sent']>0 else 0:.2f}%")
    print(f" Runtime: {int(time()-start_time)//3600}h {int((time()-start_time)%3600)//60}m {int((time()-start_time)%60)}s")
    print("\n" + "="*70)
