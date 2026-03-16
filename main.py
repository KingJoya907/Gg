# Telegram Views Booster - Updated March 2026
# نکات مهم: 
# 1. حتماً config.ini با منابع پروکسی فعال داشته باش (proxifly + proxyscrape اولویت)
# 2. THREADS رو بیشتر از ۵۰ نذار → تلگرام سریع بلاک می‌کنه
# 3. برای نتیجه بهتر: SOCKS5 residential بخر (رایگان تقریباً کار نمی‌کنه)

import os
import random
import requests
from time import sleep
from configparser import ConfigParser
from os import system, name
from threading import Thread, active_count
from re import search, compile

# نصب خودکار اگر نباشه
try:
    import requests
except ImportError:
    os.system('pip install requests')
    import requests

# تنظیمات اصلی
THREADS = 40                  # حداکثر ترد همزمان - بیشتر خطر بلاک
PROXIES_TYPES = ('http', 'socks4', 'socks5')
TIME_OUT = 8                  # ثانیه - کمتر از ۱۰ بهتره

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0',
    # می‌تونی بیشتر اضافه کنی
]

REGEX = compile(r"(?:^|\D)?(("+ r"(?:[1-9]|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"):" + (r"(?:\d|[1-9]\d{1,3}|[1-5]\d{4}|6[0-4]\d{3}"
                + r"|65[0-4]\d{2}|655[0-2]\d|6553[0-5])")
                + r")(?:\D|$)")

# فایل‌ها و متغیرها
errors_file = open('errors.txt', 'a+', encoding='utf-8')
success_views = 0
proxy_errors = 0
token_errors = 0

cfg = ConfigParser(interpolation=None)
cfg.read("config.ini", encoding="utf-8")

try:
    http_sec = cfg["HTTP"]
    socks4_sec = cfg["SOCKS4"]
    socks5_sec = cfg["SOCKS5"]
except KeyError:
    print(" [ ERROR ] config.ini پیدا نشد یا بخش‌ها کامل نیست!")
    sleep(5)
    exit()

http_proxies = []
socks4_proxies = []
socks5_proxies = []

channel = ""
post = ""

def get_random_ua():
    return random.choice(USER_AGENTS)

def is_proxy_alive(proxy_str, proxy_type, test_url="https://t.me", timeout=6):
    try:
        proxies = {
            'http': f'{proxy_type}://{proxy_str}',
            'https': f'{proxy_type}://{proxy_str}'
        }
        r = requests.get(test_url, proxies=proxies, timeout=timeout, headers={'User-Agent': get_random_ua()})
        return r.status_code in (200, 301, 302)
    except:
        return False

def scrap(sources_list, proxy_type):
    for url in sources_list:
        url = url.strip()
        if not url:
            continue
        try:
            resp = requests.get(url, timeout=TIME_OUT, headers={'User-Agent': get_random_ua()})
            resp.raise_for_status()
            matches = REGEX.findall(resp.text)
            for match in matches:
                proxy = match[0]  # گروه کامل IP:PORT
                if proxy_type == 'http':
                    http_proxies.append(proxy)
                elif proxy_type == 'socks4':
                    socks4_proxies.append(proxy)
                elif proxy_type == 'socks5':
                    socks5_proxies.append(proxy)
        except Exception as ex:
            errors_file.write(f"Scrape failed {url} → {ex}\n")

def start_scrap_and_filter():
    global http_proxies, socks4_proxies, socks5_proxies
    http_proxies.clear()
    socks4_proxies.clear()
    socks5_proxies.clear()

    threads = []

    for section, ptype in [
        (http_sec.get("Sources", ""), 'http'),
        (socks4_sec.get("Sources", ""), 'socks4'),
        (socks5_sec.get("Sources", ""), 'socks5')
    ]:
        sources = [s.strip() for s in section.splitlines() if s.strip()]
        if sources:
            t = Thread(target=scrap, args=(sources, ptype))
            threads.append(t)
            t.start()

    for t in threads:
        t.join()

    print("\n[*] فیلتر کردن پروکسی‌های زنده ... (ممکن است چند دقیقه طول بکشد)")
    
    http_proxies = [p for p in http_proxies if is_proxy_alive(p, 'http')]
    socks4_proxies = [p for p in socks4_proxies if is_proxy_alive(p, 'socks4')]
    socks5_proxies = [p for p in socks5_proxies if is_proxy_alive(p, 'socks5')]

    total_alive = len(http_proxies) + len(socks4_proxies) + len(socks5_proxies)
    print(f"[+] پروکسی زنده پیدا شد: HTTP={len(http_proxies)} | S4={len(socks4_proxies)} | S5={len(socks5_proxies)} | جمع={total_alive}")

def get_view_token(proxy, ptype):
    global token_errors
    try:
        s = requests.Session()
        headers = {
            'User-Agent': get_random_ua(),
            'Referer': f'https://t.me/{channel}/{post}'
        }
        r = s.get(
            f"https://t.me/{channel}/{post}",
            params={'embed': '1', 'mode': 'tme'},
            headers=headers,
            proxies={'http': f'{ptype}://{proxy}', 'https': f'{ptype}://{proxy}'},
            timeout=TIME_OUT
        )
        m = search(r'data-view="([^"]+)"', r.text)
        if m:
            return m.group(1), s
        token_errors += 1
        return None
    except Exception as e:
        errors_file.write(f"Token error {proxy} → {e}\n")
        token_errors += 1
        return None

def send_view(token, session, proxy, ptype):
    global success_views, proxy_errors
    try:
        ck = session.cookies.get_dict()
        headers = {
            'User-Agent': get_random_ua(),
            'Referer': f'https://t.me/{channel}/{post}?embed=1&mode=tme',
            'X-Requested-With': 'XMLHttpRequest'
        }
        r = session.get(
            "https://t.me/v/",
            params={'views': token},
            headers=headers,
            cookies={
                'stel_dt': '-240',
                'stel_web_auth': 'https%3A%2F%2Fweb.telegram.org%2Fz%2F',
                'stel_ssid': ck.get('stel_ssid'),
                'stel_on': ck.get('stel_on')
            },
            proxies={'http': f'{ptype}://{proxy}', 'https': f'{ptype}://{proxy}'},
            timeout=TIME_OUT
        )
        if r.status_code == 200 and r.text.strip() == 'true':
            success_views += 1
            print(f"[OK] بازدید ارسال شد → جمع موفق: {success_views} | {proxy}")
            return True
        proxy_errors += 1
        return False
    except Exception as e:
        errors_file.write(f"Send view error {proxy} → {e}\n")
        proxy_errors += 1
        return False

def process_proxy(proxy, ptype):
    token_data = get_view_token(proxy, ptype)
    if token_data:
        send_view(token_data[0], token_data[1], proxy, ptype)
    sleep(random.uniform(1.8, 6.5))   # تأخیر تصادفی مهم است

def views_loop():
    while True:
        start_scrap_and_filter()
        if not (http_proxies or socks4_proxies or socks5_proxies):
            print("[!] هیچ پروکسی زنده‌ای پیدا نشد → ۳۰ ثانیه صبر...")
            sleep(30)
            continue

        print("\n[*] شروع ارسال بازدید...")
        threads = []
        idx = 0
        all_proxies = [
            (p, 'http') for p in http_proxies
        ] + [
            (p, 'socks4') for p in socks4_proxies
        ] + [
            (p, 'socks5') for p in socks5_proxies
        ]

        for proxy, ptype in all_proxies:
            t = Thread(target=process_proxy, args=(proxy, ptype))
            threads.append(t)
            while active_count() > THREADS + 2:   # +2 برای margin
                sleep(0.1)
            t.start()

        for t in threads:
            t.join()

        print(f"[CYCLE END] موفق: {success_views} | خطا پروکسی: {proxy_errors} | خطا توکن: {token_errors}")
        sleep(15)  # فاصله بین دورها

def monitor_real_views():
    while True:
        try:
            r = requests.get(
                f"https://t.me/{channel}/{post}",
                params={'embed': '1', 'mode': 'tme'},
                headers={'User-Agent': get_random_ua()},
                timeout=10
            )
            m = search(r'<span class="tgme_widget_message_views">([^<]+)', r.text)
            if m:
                views = m.group(1).strip()
                print(f"[REAL VIEWS] بازدید واقعی فعلی: {views}")
        except:
            pass
        sleep(random.uniform(5, 15))

# شروع برنامه
system('cls' if name == 'nt' else 'clear')
print("=== Telegram Views Booster 2026 Edition ===\n")

url_input = input("لینک پست تلگرام را وارد کنید (مثال: https://t.me/channel/123) : ").strip()
if "https://t.me/" in url_input:
    url_input = url_input.replace("https://t.me/", "")
channel, post = url_input.split("/", 1)

print(f"\nهدف → کانال: {channel} | پست: {post}\n")

Thread(target=views_loop, daemon=True).start()
Thread(target=monitor_real_views, daemon=True).start()

try:
    while True:
        sleep(1)
except KeyboardInterrupt:
    print("\n[!] برنامه متوقف شد توسط کاربر")
    print(f"جمع بازدیدهای موفق: {success_views}")
    print(f"خطاهای پروکسی: {proxy_errors} | خطاهای توکن: {token_errors}")
    errors_file.close()
