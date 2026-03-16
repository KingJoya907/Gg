import os
try:
    import requests
    from time import sleep, time
    from configparser import ConfigParser
    from os import system, name
    from threading import Thread, active_count
    from re import search, compile
    from queue import Queue
    import concurrent.futures
except:
    os.system('pip install requests')
    os.system('pip install configparser')

THREADS = 1000  # افزایش تعداد نخ‌ها
PROXIES_TYPES = ('http', 'socks4', 'socks5')
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36'
BATCH_SIZE = 100  # اندازه دسته برای پردازش گروهی

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
channel, post, time_out, real_views = '', 0, 10, 0  # کاهش timeout

def scrap_batch(sources, _proxy_type):
    """استخراج پروکسی به صورت دسته‌ای"""
    proxies = []
    session = requests.Session()
    
    for source in sources:
        if source:
            try:
                response = session.get(source, timeout=time_out)
                if response.status_code == 200:
                    matches = REGEX.finditer(response.text)
                    for match in matches:
                        proxies.append(match.group(1))
            except Exception as e:
                errors.write(f'{e}\n')
    
    return proxies, _proxy_type

def start_scrap():
    """شروع استخراج با ThreadPoolExecutor"""
    http_proxies.clear()
    socks4_proxies.clear()
    socks5_proxies.clear()
    
    sources_list = [
        (http.get("Sources").splitlines(), 'http'),
        (socks4.get("Sources").splitlines(), 'socks4'),
        (socks5.get("Sources").splitlines(), 'socks5')
    ]
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for sources, proxy_type in sources_list:
            # تقسیم به دسته‌های کوچکتر
            for i in range(0, len(sources), BATCH_SIZE):
                batch = sources[i:i + BATCH_SIZE]
                futures.append(executor.submit(scrap_batch, batch, proxy_type))
        
        for future in concurrent.futures.as_completed(futures):
            proxies, proxy_type = future.result()
            if proxy_type == 'http':
                http_proxies.extend(proxies)
            elif proxy_type == 'socks4':
                socks4_proxies.extend(proxies)
            elif proxy_type == 'socks5':
                socks5_proxies.extend(proxies)

def get_token(proxy, proxy_type):
    """دریافت توکن با استفاده از connection pooling"""
    try:
        session = requests.Session()
        
        # ایجاد connection pool
        adapter = requests.adapters.HTTPAdapter(pool_connections=100, pool_maxsize=100)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        
        response = session.get(
            f'https://t.me/{channel}/{post}',
            params={'embed': '1', 'mode': 'tme'},
            headers={
                'referer': f'https://t.me/{channel}/{post}',
                'user-agent': USER_AGENT,
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'accept-language': 'en-US,en;q=0.5',
                'accept-encoding': 'gzip, deflate',
                'connection': 'keep-alive',
            },
            proxies={
                'http': f'{proxy_type}://{proxy}',
                'https': f'{proxy_type}://{proxy}'
            },
            timeout=time_out,
            stream=False)

        if response.status_code == 200:
            token_match = search('data-view="([^"]+)', response.text)
            if token_match:
                return token_match.group(1), session
        
        return None

    except Exception:
        return None

def send_view_batch(token_sessions):
    """ارسال بازدید به صورت دسته‌ای"""
    results = []
    
    for token, session, proxy, proxy_type in token_sessions:
        try:
            cookies_dict = session.cookies.get_dict()
            
            response = session.get(
                'https://t.me/v/',
                params={'views': str(token)},
                cookies={
                    'stel_dt': '-240',
                    'stel_web_auth': 'https%3A%2F%2Fweb.telegram.org%2Fz%2F',
                    'stel_ssid': cookies_dict.get('stel_ssid', ''),
                    'stel_on': cookies_dict.get('stel_on', '')
                },
                headers={
                    'referer': f'https://t.me/{channel}/{post}?embed=1&mode=tme',
                    'user-agent': USER_AGENT,
                    'x-requested-with': 'XMLHttpRequest',
                    'connection': 'keep-alive',
                },
                proxies={
                    'http': f'{proxy_type}://{proxy}',
                    'https': f'{proxy_type}://{proxy}'
                },
                timeout=time_out)

            if response.status_code == 200 and response.text == 'true':
                results.append(True)
            else:
                results.append(False)

        except Exception:
            results.append(False)
    
    return results

def worker(proxy_queue):
    """کارگر برای پردازش پروکسی‌ها"""
    global proxy_errors, token_errors
    
    while not proxy_queue.empty():
        try:
            proxy, proxy_type = proxy_queue.get_nowait()
            
            token_data = get_token(proxy, proxy_type)
            
            if token_data:
                token, session = token_data
                # ارسال بازدید
                result = send_view_batch([(token, session, proxy, proxy_type)])
                if not result[0]:
                    proxy_errors += 1
            else:
                token_errors += 1
                
        except:
            proxy_errors += 1
        finally:
            proxy_queue.task_done()

def start_view():
    """شروع با معماری مبتنی بر صف"""
    global proxy_errors, token_errors
    
    start_scrap()
    
    # ایجاد صف پروکسی‌ها
    proxy_queue = Queue()
    
    # اضافه کردن پروکسی‌ها به صف
    for i, proxies in enumerate([http_proxies, socks4_proxies, socks5_proxies]):
        proxy_type = PROXIES_TYPES[i]
        for proxy in proxies:
            proxy_queue.put((proxy, proxy_type))
    
    # ایجاد و شروع نخ‌ها
    threads = []
    for _ in range(min(THREADS, proxy_queue.qsize())):
        thread = Thread(target=worker, args=(proxy_queue,))
        thread.daemon = True
        thread.start()
        threads.append(thread)
    
    # منتظر ماندن برای اتمام کار
    proxy_queue.join()
    
    # نمایش آمار
    print(f"\rViews: {real_views} | Proxy Errors: {proxy_errors} | Token Errors: {token_errors}", end="")
    
    # شروع مجدد
    start_view()

def check_views():
    """بررسی تعداد بازدیدها"""
    global real_views
    session = requests.Session()
    
    while True:
        try:
            response = session.get(
                f'https://t.me/{channel}/{post}',
                params={'embed': '1', 'mode': 'tme'},
                headers={
                    'referer': f'https://t.me/{channel}/{post}',
                    'user-agent': USER_AGENT
                },
                timeout=5)

            views_match = search('<span class="tgme_widget_message_views">([^<]+)', response.text)
            if views_match:
                real_views = views_match.group(1)
            
            sleep(1)

        except:
            pass

# پاکسازی صفحه
system('cls' if name == 'nt' else 'clear')

# دریافت لینک
url = input("TeleGram View Post URL ==> ").replace('https://t.me/', '')
channel, post = url.split('/')

# شروع نخ‌ها
Thread(target=start_view, daemon=True).start()
Thread(target=check_views, daemon=True).start()

# نگه داشتن برنامه
try:
    while True:
        sleep(1)
except KeyboardInterrupt:
    print("\nStopping...")
