import os
import random
import requests
from time import sleep
from configparser import ConfigParser
from os import system, name
from threading import Thread, active_count
from re import search, compile

try:
    import requests
except:
    os.system('pip install requests')
    import requests

THREADS = 40               # خیلی مهم: بیشتر از ۵۰ نذار، بلاک می‌شی
PROXIES_TYPES = ('http', 'socks4', 'socks5')
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
    # می‌تونی ۱۰–۲۰ تا دیگه اضافه کنی
]

REGEX = compile(r"(?:^|\D)?(("+ r"(?:[1-9]|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"):" + (r"(?:\d|[1-9]\d{1,3}|[1-5]\d{4}|6[0-4]\d{3}"
                + r"|65[0-4]\d{2}|655[0-2]\d|6553[0-5])")
                + r")(?:\D|$)")

errors = open('errors.txt', 'a+', encoding='utf-8')
success_views = 0          # شمارنده views موفق
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
channel, post = '', ''
time_out = 8               # کمتر بهتره

def get_random_ua():
    return random.choice(USER_AGENTS)

def is_proxy_alive(proxy, proxy_type, test_url="https://t.me", timeout=6):
    try:
        resp = requests.get(test_url, proxies={
            'http': f'{proxy_type}://{proxy}',
            'https': f'{proxy_type}://{proxy}'
        }, timeout=timeout, headers={'User-Agent': get_random_ua()})
        return resp.status_code in (200, 302, 301)
    except:
        return False

def scrap(sources, _proxy_type):
    for source in sources:
        if not source.strip(): continue
        try:
            response = requests.get(source.strip(), timeout=time_out, headers={'User-Agent': get_random_ua()})
            response.raise_for_status()
            found = REGEX.findall(response.text)
            for proxy in found:
                if _proxy_type == 'http':
                    http_proxies.append(proxy)
                elif _proxy_type == 'socks4':
                    socks4_proxies.append(proxy)
                elif _proxy_type == 'socks5':
                    socks5_proxies.append(proxy)
        except Exception as e:
            errors.write(f'Scrape error {source}: {e}\n')

def start_scrap():
    for lst in (http_proxies, socks4_proxies, socks5_proxies):
        lst.clear()

    threads = []
    for sources, ptype in [
        (http.get("Sources", "").splitlines(), 'http'),
        (socks4.get("Sources", "").splitlines(), 'socks4'),
        (socks5.get("Sources", "").splitlines(), 'socks5')
    ]:
        t = Thread(target=scrap, args=(sources, ptype))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # فیلتر پروکسی‌های زنده (خیلی مهم!)
    print("[*] Filtering alive proxies...")
    http_proxies[:] = [p for p in http_proxies if is_proxy_alive(p, 'http')]
    socks4_proxies[:] = [p for p in socks4_proxies if is_proxy_alive(p, 'socks4')]
    socks5_proxies[:] = [p for p in socks5_proxies if is_proxy_alive(p, 'socks5')]
    print(f"[+] Alive: HTTP={len(http_proxies)} | SOCKS4={len(socks4_proxies)} | SOCKS5={len(socks5_proxies)}")

def get_token(proxy, proxy_type):
    global token_errors
    try:
        session = requests.Session()
        headers = {
            'referer': f'https://t.me/{channel}/{post}',
            'user-agent': get_random_ua()
        }
        response = session.get(
            f'https://t.me/{channel}/{post}',
            params={'embed': '1', 'mode': 'tme'},
            headers=headers,
            proxies={
                'http': f'{proxy_type}://{proxy}',
                'https': f'{proxy_type}://{proxy}'
            },
            timeout=time_out
        )
        match = search('data-view="([^"]+)', response.text)
        if match:
            return match.group(1), session
        else:
            token_errors += 1
            return None
    except Exception as e:
        errors.write(f'Get token error: {e}\n')
        return None

def send_view(token, session, proxy, proxy_type):
    global success_views, proxy_errors
    try:
        cookies_dict = session.cookies.get_dict()
        headers = {
            'referer': f'https://t.me/{channel}/{post}?embed=1&mode=tme',
            'user-agent': get_random_ua(),
            'x-requested-with': 'XMLHttpRequest'
        }
        response = session.get(
            'https://t.me/v/',
            params={'views': str(token)},
            cookies={
                'stel_dt': '-240',
                'stel_web_auth': 'https%3A%2F%2Fweb.telegram.org%2Fz%2F',
                'stel_ssid': cookies_dict.get('stel_ssid'),
                'stel_on': cookies_dict.get('stel_on')
            },
            headers=headers,
            proxies={
                'http': f'{proxy_type}://{proxy}',
                'https': f'{proxy_type}://{proxy}'
            },
            timeout=time_out
        )
        if response.status_code == 200 and response.text == 'true':
            success_views += 1
            print(f"[SUCCESS] View sent! Total: {success_views}")
            return True
        else:
            proxy_errors += 1
            return False
    except Exception as e:
        errors.write(f'Send view error: {e}\n')
        proxy_errors += 1
        return False

def control(proxy, proxy_type):
    token_data = get_token(proxy, proxy_type)
    if token_data:
        send_view(token_data[0], token_data[1], proxy, proxy_type)
    sleep(random.uniform(1.5, 5.0))  # جلوگیری از rate-limit

def start_view():
    while True:
        start_scrap()
        print("[*] Starting view threads...")
        c = 0
        threads = []
        for proxies_list in [http_proxies, socks4_proxies, socks5_proxies]:
            for proxy in proxies_list:
                t = Thread(target=control, args=(proxy, PROXIES_TYPES[c]))
                threads.append(t)
                while active_count() > THREADS:
                    sleep(0.1)
                t.start()
            c += 1
            sleep(3)  # فاصله بین پروتکل‌ها

        for t in threads:
            t.join()
        print("[*] Cycle finished. Restarting scrape...")
        sleep(10)

def check_views():
    global real_views
    while True:
        try:
            req = requests.get(
                f'https://t.me/{channel}/{post}',
                params={'embed': '1', 'mode': 'tme'},
                headers={'user-agent': get_random_ua()}
            )
            match = search(r'<span class="tgme_widget_message_views">([^<]+)', req.text)
            if match:
                real_views = match.group(1)
                print(f"[VIEWS] Current real views: {real_views}")
        except:
            pass
        sleep(random.uniform(4, 10))

system('cls' if name == 'nt' else 'clear')
print("Telegram View Booster - Updated 2026")

url = input("TeleGram View Post URL ==> ").strip()
if 'https://t.me/' in url:
    url = url.replace('https://t.me/', '')
channel, post = url.split('/')

print(f"[TARGET] Channel: {channel} | Post: {post}")

Thread(target=start_view, daemon=True).start()
Thread(target=check_views, daemon=True).start()

# نگه داشتن برنامه باز
try:
    while True:
        sleep(1)
except KeyboardInterrupt:
    print("\n[!] Stopped by user. Total success views:", success_views)
    errors.close()
