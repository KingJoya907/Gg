import os
try:
    import requests
    from time import sleep
    from configparser import ConfigParser
    from os import system, name
    from threading import Thread, active_count
    from re import search, compile
    import random
    from fake_useragent import UserAgent
    import concurrent.futures  # جدید برای چک موازی
    import time
except:
    os.system('pip install requests')
    os.system('pip install configparser')
    os.system('pip install fake-useragent')

THREADS = 500
PROXIES_TYPES = ('http', 'socks4', 'socks5')

# User-Agent generator
try:
    ua = UserAgent()
    def get_ua():
        return ua.random
except:
    # Fallback if fake-useragent fails
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
    ]
    def get_ua():
        return random.choice(USER_AGENTS)

REGEX = compile(r"(?:^|\D)?(("+ r"(?:[1-9]|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"):" + (r"(?:\d|[1-9]\d{1,3}|[1-5]\d{4}|6[0-4]\d{3}"
                + r"|65[0-4]\d{2}|655[0-2]\d|6553[0-5])")
                + r")(?:\D|$)")

errors = open('errors.txt', 'a+')
cfg = ConfigParser(interpolation=None)
cfg.read("config.ini", encoding="utf-8")

http, socks4, socks5 = '', '', ''
try:
    http, socks4, socks5 = cfg["HTTP"], cfg["SOCKS4"], cfg["SOCKS5"]
except KeyError:
    print(' [ OUTPUT ] Error | config.ini not found!')
    sleep(3)
    exit()

http_proxies, socks4_proxies, socks5_proxies = [], [], []
proxy_errors, token_errors = 0, 0
total_views_sent = 0
successful_views = 0
channel, post, time_out, real_views = '', 0, 15, 0


def scrap(sources, _proxy_type):
    for source in sources:
        if source:
            try:
                response = requests.get(source, timeout=time_out)
            except Exception as e:
                errors.write(f'{e}\n')

            if tuple(REGEX.finditer(response.text)):
                for proxy in tuple(REGEX.finditer(response.text)):
                    if _proxy_type == 'http':
                        http_proxies.append(proxy.group(1))
                    elif _proxy_type == 'socks4':
                        socks4_proxies.append(proxy.group(1))
                    elif _proxy_type == 'socks5':
                        socks5_proxies.append(proxy.group(1))


def start_scrap():
    threads = []
    for i in (http_proxies, socks4_proxies, socks5_proxies):
        i.clear()

    for i in ((http.get("Sources").splitlines(), 'http'),
              (socks4.get("Sources").splitlines(), 'socks4'),
              (socks5.get("Sources").splitlines(), 'socks5')):

        thread = Thread(target=scrap, args=(i[0], i[1]))
        threads.append(thread)
        thread.start()

    for t in threads:
        t.join()


# تابع جدید: چک پروکسی زنده
def check_proxy(proxy, proxy_type, test_url="https://httpbin.org/ip", timeout=6, retries=1):
    proxies = {
        'http': f'{proxy_type}://{proxy}',
        'https': f'{proxy_type}://{proxy}'
    }
    
    for attempt in range(retries + 1):
        try:
            start_time = time.time()
            r = requests.get(
                test_url,
                proxies=proxies,
                timeout=(timeout, timeout + 2),
                allow_redirects=True
            )
            if r.status_code == 200:
                elapsed = time.time() - start_time
                if elapsed < timeout:
                    return proxy, True, round(elapsed, 2)
        except:
            pass
        time.sleep(0.3)
    
    return proxy, False, 0


def get_token(proxy, proxy_type):
    try:
        session = requests.session()
        current_ua = get_ua()

        response = session.get(
            f'https://t.me/{channel}/{post}',
            params={'embed': '1', 'mode': 'tme'},
            headers={
                'referer': f'https://t.me/{channel}/{post}',
                'user-agent': current_ua
            },
            proxies={
                'http': f'{proxy_type}://{proxy}',
                'https': f'{proxy_type}://{proxy}'
            },
            timeout=time_out)

        return search('data-view="([^"]+)', response.text).group(1), session

    except AttributeError:
        return 2
    except requests.exceptions.RequestException:
        return 1
    except Exception as e:
        return errors.write(f'{e}\n')


def send_view(token, session, proxy, proxy_type):
    global total_views_sent, successful_views
    
    try:
        cookies_dict = session.cookies.get_dict()
        current_ua = get_ua()

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
                'user-agent': current_ua,
                'x-requested-with': 'XMLHttpRequest'
            },
            proxies={
                'http': f'{proxy_type}://{proxy}',
                'https': f'{proxy_type}://{proxy}'
            },
            timeout=time_out)

        total_views_sent += 1
        if response.status_code == 200 and response.text == 'true':
            successful_views += 1
            return True
        else:
            return False

    except requests.exceptions.RequestException:
        return 1
    except Exception:
        pass


def control(proxy, proxy_type):
    global proxy_errors, token_errors

    token_data = get_token(proxy, proxy_type)

    if token_data == 2:
        token_errors += 1
    elif token_data == 1:
        proxy_errors += 1
    elif token_data:
        send_data = send_view(token_data[0], token_data[1], proxy, proxy_type)
        if send_data == 1:
            proxy_errors += 1


def print_stats():
    from datetime import datetime
    start_time = datetime.now()
    
    while True:
        system('cls' if name == 'nt' else 'clear')
        
        elapsed = datetime.now() - start_time
        hours = int(elapsed.total_seconds() // 3600)
        minutes = int((elapsed.total_seconds() % 3600) // 60)
        seconds = int(elapsed.total_seconds() % 60)
        
        current_speed = successful_views / (elapsed.total_seconds() + 0.1)
        success_rate = (successful_views / (total_views_sent + 0.1)) * 100
        
        total_proxies = len(http_proxies) + len(socks4_proxies) + len(socks5_proxies)
        
        print("╔" + "═" * 60 + "╗")
        print("║" + " " * 15 + "🔥 TELEGRAM VIEW BOT ULTIMATE 🔥" + " " * 14 + "║")
        print("╠" + "═" * 60 + "╣")
        print(f"║ 📌 TARGET     : {channel}/{post:<30} ║")
        print(f"║ 👁️  CURRENT    : {str(real_views):<10} views{' ' * 30}║")
        print("╠" + "═" * 60 + "╣")
        print(f"║ ✅ SUCCESS     : {successful_views:>10,} views{' ' * 31}║")
        print(f"║ 🔄 TOTAL SENT  : {total_views_sent:>10,} requests{' ' * 29}║")
        print(f"║ ❌ PROXY ERR   : {proxy_errors:>10,}{' ' * 38}║")
        print(f"║ ⚠️  TOKEN ERR   : {token_errors:>10,}{' ' * 38}║")
        print("╠" + "═" * 60 + "╣")
        print(f"║ ⚡ SPEED        : {current_speed:>8.2f} views/sec{' ' * 28}║")
        print(f"║ 📊 SUCCESS RATE : {success_rate:>8.2f}%{' ' * 31}║")
        print("╠" + "═" * 60 + "╣")
        print(f"║ 🌐 HTTP PROXIES : {len(http_proxies):>8,}{' ' * 35}║")
        print(f"║ 🔷 SOCKS4       : {len(socks4_proxies):>8,}{' ' * 35}║")
        print(f"║ 🔶 SOCKS5       : {len(socks5_proxies):>8,}{' ' * 35}║")
        print(f"║ 📦 TOTAL PROXIES: {total_proxies:>8,}{' ' * 35}║")
        print("╠" + "═" * 60 + "╣")
        print(f"║ ⏱️  RUNTIME      : {hours:02d}:{minutes:02d}:{seconds:02d}{' ' * 33}║")
        print("╚" + "═" * 60 + "╝")
        
        thread_count = active_count()
        print(f"\n🔧 Active Threads: {thread_count:,} | ⚙️  Max Threads: {THREADS}")
        print(f"🔄 Last User-Agent: {get_ua()[:30]}...")
        
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
                    'user-agent': get_ua()
                })

            real_views = search(
                '<span class="tgme_widget_message_views">([^<]+)',
                telegram_request.text).group(1)

            sleep(2)

        except:
            pass


def start_view():
    global http_proxies, socks4_proxies, socks5_proxies
    
    c, threads = 0, []
    start_scrap()

    # مرحله چک پروکسی (جدید)
    print("\n[CHECK] شروع چک پروکسی‌های زنده ... (ممکن است ۱-۵ دقیقه طول بکشد)")
    
    all_proxies = []
    for proxies_list, p_type in [(http_proxies, 'http'), (socks4_proxies, 'socks4'), (socks5_proxies, 'socks5')]:
        all_proxies.extend([(p, p_type) for p in proxies_list])
    
    good_proxies = {'http': [], 'socks4': [], 'socks5': []}
    
    if not all_proxies:
        print("[CHECK] هیچ پروکسی‌ای جمع‌آوری نشد! لیست sources در config.ini را چک کنید.")
        return
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=150) as executor:
        future_to_proxy = {
            executor.submit(check_proxy, proxy, p_type): (proxy, p_type)
            for proxy, p_type in all_proxies[:4000]  # محدود به ۴۰۰۰ تا اول برای سرعت
        }
        
        for future in concurrent.futures.as_completed(future_to_proxy):
            proxy, p_type = future_to_proxy[future]
            try:
                proxy_str, alive, speed = future.result()
                if alive:
                    good_proxies[p_type].append(proxy_str)
                    # print(f"[LIVE {p_type.upper()}] {proxy_str} ({speed}s)")  # اگر می‌خوای چاپ کن، کامنت رو بردار
            except:
                pass
    
    # جایگزین لیست اصلی با زنده‌ها
    http_proxies = good_proxies['http']
    socks4_proxies = good_proxies['socks4']
    socks5_proxies = good_proxies['socks5']
    
    total_good = len(http_proxies) + len(socks4_proxies) + len(socks5_proxies)
    print(f"[CHECK DONE] {total_good:,} پروکسی زنده پیدا شد (HTTP: {len(http_proxies):,} | SOCKS4: {len(socks4_proxies):,} | SOCKS5: {len(socks5_proxies):,})")
    
    if total_good == 0:
        print("هیچ پروکسی زنده‌ای پیدا نشد! لیست‌ها را بروزرسانی کنید یا timeout_check را افزایش دهید.")
        return
    
    # حالا ارسال ویو با پروکسی‌های زنده
    for i in [http_proxies, socks4_proxies, socks5_proxies]:
        for j in i:
            thread = Thread(target=control, args=(j, PROXIES_TYPES[c]))
            threads.append(thread)

            while active_count() > THREADS:
                sleep(0.05)

            thread.start()

        c += 1
        sleep(2)

    for t in threads:
        t.join()
        start_view()  # اگر می‌خوای لوپ بی‌نهایت ادامه بده


system('cls' if name == 'nt' else 'clear')

channel, post = input("🔥 Telegram View Post URL ==> ").replace('https://t.me/', '').split('/')

print("\n" + "=" * 50)
print("🚀 INITIALIZING ULTIMATE VIEW BOT...")
print("📡 COLLECTING PROXIES...")
print("⚡ PREPARING THREADS...")
print("=" * 50 + "\n")
sleep(2)

# شروع همه تردها
Thread(target=start_view).start()
Thread(target=check_views).start()
Thread(target=print_stats).start()
