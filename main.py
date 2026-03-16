"""
TELEGRAM VIEW BOT - ULTIMATE EDITION
تمامی حقوق محفوظ است - نسخه نهایی 2026
"""

import os
import sys
import time
import random
import threading
from datetime import datetime, timedelta
from threading import Thread, active_count
from re import search, compile
from collections import deque

# نصب خودکار کتابخانه‌ها
required_packages = ['requests', 'configparser', 'fake-useragent', 'psutil', 'colorama']

for package in required_packages:
    try:
        __import__(package.replace('-', '_'))
    except ImportError:
        print(f"📦 Installing {package}...")
        os.system(f'pip install {package} -q')

import requests
from time import sleep
from configparser import ConfigParser
from os import system, name
from fake_useragent import UserAgent
import psutil
from colorama import init, Fore, Style

# تنظیمات اولیه
init(autoreset=True)
system('cls' if name == 'nt' else 'clear')

# ==================== تنظیمات اصلی ====================
THREADS = 1000
PROXIES_TYPES = ('http', 'socks4', 'socks5')
time_out = 8
proxy_update_interval = 300  # 5 دقیقه
max_proxies_per_type = 3000

# ==================== User-Agent هوشمند ====================
try:
    ua = UserAgent()
    def get_ua():
        return ua.random
except:
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
    ]
    def get_ua():
        return random.choice(USER_AGENTS)

# ==================== Regex برای استخراج پروکسی ====================
REGEX = compile(r"(?:^|\D)?(("+ r"(?:[1-9]|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"):" + (r"(?:\d|[1-9]\d{1,3}|[1-5]\d{4}|6[0-4]\d{3}"
                + r"|65[0-4]\d{2}|655[0-2]\d|6553[0-5])")
                + r")(?:\D|$)")

# ==================== فایل خطاها ====================
errors = open('errors.txt', 'a+', encoding='utf-8')

# ==================== بارگذاری config.ini ====================
cfg = ConfigParser(interpolation=None)
cfg.read("config.ini", encoding="utf-8")

try:
    http = cfg["HTTP"]
    socks4 = cfg["SOCKS4"]
    socks5 = cfg["SOCKS5"]
except KeyError:
    print(Fore.RED + "❌ Error | config.ini not found!")
    print(Fore.YELLOW + "📝 Creating default config.ini...")
    
    # ساخت فایل config.ini پیش‌فرض
    default_config = """[HTTP]
Sources =
    https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt
    https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt
    https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=5000&country=all
    https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt

[SOCKS4]
Sources =
    https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt
    https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks4.txt
    https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks4&timeout=5000
    https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks4.txt

[SOCKS5]
Sources =
    https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt
    https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks5.txt
    https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks5&timeout=5000
    https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt
"""
    with open('config.ini', 'w', encoding='utf-8') as f:
        f.write(default_config)
    
    print(Fore.GREEN + "✅ config.ini created! Please edit it and restart.")
    sleep(5)
    exit()

# ==================== متغیرهای سراسری ====================
http_proxies = []
socks4_proxies = []
socks5_proxies = []
proxy_errors = 0
token_errors = 0
total_views_sent = 0
successful_views = 0
channel = ''
post = 0
real_views = 0
last_proxy_update = datetime.now()
proxy_scores = {}
proxy_failures = {}
proxy_success = {}
view_history = deque(maxlen=100)
success_history = deque(maxlen=100)
start_time = datetime.now()

# ==================== توابع مدیریت پروکسی ====================

def validate_proxy(proxy, proxy_type, timeout=3):
    """اعتبارسنجی پروکسی"""
    try:
        test_url = "http://httpbin.org/ip"
        proxies = {
            'http': f'{proxy_type}://{proxy}',
            'https': f'{proxy_type}://{proxy}'
        }
        response = requests.get(test_url, proxies=proxies, timeout=timeout, headers={'User-Agent': get_ua()})
        return response.status_code == 200
    except:
        return False

def score_proxy(proxy, proxy_type, success):
    """امتیازدهی به پروکسی"""
    key = f"{proxy_type}:{proxy}"
    
    if key not in proxy_scores:
        proxy_scores[key] = 50
        proxy_failures[key] = 0
        proxy_success[key] = 0
    
    if success:
        proxy_success[key] += 1
        proxy_scores[key] = min(100, proxy_scores[key] + 2)
        proxy_failures[key] = max(0, proxy_failures[key] - 1)
        return True
    else:
        proxy_failures[key] += 1
        proxy_scores[key] = max(0, proxy_scores[key] - 5)
        
        if proxy_failures[key] > 3 or proxy_scores[key] < 30:
            remove_proxy(proxy, proxy_type)
            return False
    return True

def remove_proxy(proxy, proxy_type):
    """حذف پروکسی بد"""
    global http_proxies, socks4_proxies, socks5_proxies
    
    if proxy_type == 'http' and proxy in http_proxies:
        http_proxies.remove(proxy)
    elif proxy_type == 'socks4' and proxy in socks4_proxies:
        socks4_proxies.remove(proxy)
    elif proxy_type == 'socks5' and proxy in socks5_proxies:
        socks5_proxies.remove(proxy)
    
    key = f"{proxy_type}:{proxy}"
    if key in proxy_scores:
        del proxy_scores[key]

def get_best_proxy(proxy_type):
    """گرفتن بهترین پروکسی"""
    proxies = []
    if proxy_type == 'http':
        proxies = http_proxies
    elif proxy_type == 'socks4':
        proxies = socks4_proxies
    else:
        proxies = socks5_proxies
    
    if not proxies:
        return None
    
    # پروکسی‌های با امتیاز بالا
    good_proxies = []
    for proxy in proxies:
        key = f"{proxy_type}:{proxy}"
        score = proxy_scores.get(key, 50)
        if score > 60:
            good_proxies.append(proxy)
    
    if good_proxies:
        return random.choice(good_proxies)
    return random.choice(proxies)

def scrap(sources, _proxy_type):
    """جمع‌آوری پروکسی از منابع"""
    for source in sources:
        if source and source.strip():
            try:
                response = requests.get(source.strip(), timeout=time_out, headers={'User-Agent': get_ua()})
                if response.status_code == 200:
                    for proxy in REGEX.finditer(response.text):
                        proxy_str = proxy.group(1)
                        if validate_proxy(proxy_str, _proxy_type, timeout=2):
                            if _proxy_type == 'http':
                                http_proxies.append(proxy_str)
                            elif _proxy_type == 'socks4':
                                socks4_proxies.append(proxy_str)
                            elif _proxy_type == 'socks5':
                                socks5_proxies.append(proxy_str)
            except Exception as e:
                errors.write(f'{datetime.now()} - Error in scrap: {e}\n')

def start_scrap():
    """شروع جمع‌آوری همزمان"""
    threads = []
    
    # پاک کردن لیست‌ها
    http_proxies.clear()
    socks4_proxies.clear()
    socks5_proxies.clear()
    
    sources_list = [
        (http.get("Sources").splitlines() if http else [], 'http'),
        (socks4.get("Sources").splitlines() if socks4 else [], 'socks4'),
        (socks5.get("Sources").splitlines() if socks5 else [], 'socks5')
    ]
    
    for sources, ptype in sources_list:
        if sources:
            thread = Thread(target=scrap, args=(sources, ptype))
            threads.append(thread)
            thread.start()
    
    for t in threads:
        t.join()
    
    # حذف تکراری‌ها
    http_proxies[:] = list(set(http_proxies))[:max_proxies_per_type]
    socks4_proxies[:] = list(set(socks4_proxies))[:max_proxies_per_type]
    socks5_proxies[:] = list(set(socks5_proxies))[:max_proxies_per_type]

def auto_update_proxies():
    """آپدیت خودکار پروکسی‌ها"""
    global last_proxy_update
    
    while True:
        now = datetime.now()
        if (now - last_proxy_update).total_seconds() > proxy_update_interval:
            print(Fore.YELLOW + "\n🔄 Auto-updating proxies...")
            
            old_counts = {
                'http': len(http_proxies),
                'socks4': len(socks4_proxies),
                'socks5': len(socks5_proxies)
            }
            
            # جمع‌آوری پروکسی‌های جدید
            scrap_thread = Thread(target=start_scrap)
            scrap_thread.start()
            scrap_thread.join(timeout=30)
            
            print(Fore.GREEN + f"✅ Updated: HTTP: {old_counts['http']} → {len(http_proxies)}, "
                  f"SOCKS4: {old_counts['socks4']} → {len(socks4_proxies)}, "
                  f"SOCKS5: {old_counts['socks5']} → {len(socks5_proxies)}")
            
            last_proxy_update = now
        
        time.sleep(60)

# ==================== توابع اصلی ویو زدن ====================

def get_token(proxy, proxy_type):
    """گرفتن توکن ویو"""
    try:
        session = requests.Session()
        current_ua = get_ua()
        
        response = session.get(
            f'https://t.me/{channel}/{post}',
            params={'embed': '1', 'mode': 'tme'},
            headers={
                'referer': f'https://t.me/{channel}/{post}',
                'user-agent': current_ua,
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            },
            proxies={
                'http': f'{proxy_type}://{proxy}',
                'https': f'{proxy_type}://{proxy}'
            },
            timeout=time_out)

        token = search(r'data-view="(\d+)"', response.text)
        if token:
            return token.group(1), session
        return 2

    except AttributeError:
        return 2
    except requests.exceptions.RequestException:
        return 1
    except Exception as e:
        errors.write(f'{datetime.now()} - Token error: {e}\n')
        return 2

def send_view(token, session, proxy, proxy_type):
    """ارسال ویو"""
    global total_views_sent, successful_views, view_history, success_history
    
    try:
        cookies = session.cookies.get_dict()
        current_ua = get_ua()
        
        response = session.get(
            'https://t.me/v/',
            params={'views': token},
            cookies={
                'stel_dt': '-240',
                'stel_ssid': cookies.get('stel_ssid', ''),
                'stel_on': cookies.get('stel_on', '')
            },
            headers={
                'referer': f'https://t.me/{channel}/{post}?embed=1&mode=tme',
                'user-agent': current_ua,
                'x-requested-with': 'XMLHttpRequest',
                'accept': 'application/json, text/javascript, */*; q=0.01'
            },
            proxies={
                'http': f'{proxy_type}://{proxy}',
                'https': f'{proxy_type}://{proxy}'
            },
            timeout=time_out)

        total_views_sent += 1
        view_history.append(time.time())
        
        if response.status_code == 200 and response.text.strip() == 'true':
            successful_views += 1
            success_history.append(time.time())
            return True
        return False

    except requests.exceptions.RequestException:
        return 1
    except Exception as e:
        errors.write(f'{datetime.now()} - Send view error: {e}\n')
        return 1

def control(proxy, proxy_type):
    """کنترلر اصلی"""
    global proxy_errors, token_errors
    
    token_data = get_token(proxy, proxy_type)
    
    if token_data == 2:
        token_errors += 1
        score_proxy(proxy, proxy_type, False)
    elif token_data == 1:
        proxy_errors += 1
        score_proxy(proxy, proxy_type, False)
    elif token_data:
        send_result = send_view(token_data[0], token_data[1], proxy, proxy_type)
        if send_result == 1:
            proxy_errors += 1
            score_proxy(proxy, proxy_type, False)
        elif send_result:
            score_proxy(proxy, proxy_type, True)

def worker():
    """کارگر اصلی - همیشه بهترین پروکسی رو انتخاب می‌کنه"""
    while True:
        try:
            # انتخاب تصادفی نوع پروکسی
            proxy_type = random.choice(PROXIES_TYPES)
            proxy = get_best_proxy(proxy_type)
            
            if proxy:
                control(proxy, proxy_type)
            else:
                sleep(0.1)
                
        except Exception as e:
            errors.write(f'{datetime.now()} - Worker error: {e}\n')
            sleep(0.1)

def start_workers():
    """شروع کارگرها"""
    for i in range(THREADS):
        thread = Thread(target=worker, daemon=True)
        thread.start()
        if i % 100 == 0:
            sleep(0.1)

# ==================== توابع مانیتورینگ ====================

def calculate_speed(history):
    """محاسبه سرعت"""
    if len(history) < 2:
        return 0
    times = list(history)
    time_diff = times[-1] - times[0]
    if time_diff > 0:
        return len(times) / time_diff
    return 0

def check_views():
    """چک کردن ویوهای واقعی"""
    global real_views
    
    while True:
        try:
            response = requests.get(
                f'https://t.me/{channel}/{post}',
                params={'embed': '1', 'mode': 'tme'},
                headers={
                    'referer': f'https://t.me/{channel}/{post}',
                    'user-agent': get_ua()
                },
                timeout=10)

            views = search(r'<span class="tgme_widget_message_views">([^<]+)', response.text)
            if views:
                real_views = views.group(1).strip()
            sleep(3)
        except:
            sleep(5)

def display_stats():
    """نمایش آمار خفن"""
    while True:
        system('cls' if name == 'nt' else 'clear')
        
        elapsed = datetime.now() - start_time
        hours = int(elapsed.total_seconds() // 3600)
        minutes = int((elapsed.total_seconds() % 3600) // 60)
        seconds = int(elapsed.total_seconds() % 60)
        
        # محاسبه سرعت
        current_speed = calculate_speed(view_history)
        success_rate = (successful_views / total_views_sent * 100) if total_views_sent > 0 else 0
        
        # اطلاعات سیستم
        cpu = psutil.cpu_percent()
        memory = psutil.virtual_memory().percent
        
        # تعداد کل پروکسی‌ها
        total_proxies = len(http_proxies) + len(socks4_proxies) + len(socks5_proxies)
        
        # نوار پیشرفت
        def progress_bar(value, max_value, width=15):
            if max_value == 0:
                return '░' * width
            filled = int((value / max_value) * width)
            return '█' * filled + '░' * (width - filled)
        
        # ==================== نمایش باکس ====================
        print(Fore.CYAN + "╔" + "═" * 70 + "╗")
        print(Fore.CYAN + "║" + Fore.YELLOW + " " * 20 + "🔥 TELEGRAM VIEW BOT - ULTIMATE EDITION 🔥" + " " * 19 + Fore.CYAN + "║")
        print(Fore.CYAN + "╠" + "═" * 70 + "╣")
        
        # هدف
        print(Fore.CYAN + "║ " + Fore.WHITE + "📌 TARGET".ljust(12) + ":" + Fore.GREEN + f" {channel}/{post}".ljust(45) + Fore.CYAN + "║")
        print(Fore.CYAN + "║ " + Fore.WHITE + "👁️  CURRENT".ljust(12) + ":" + Fore.GREEN + f" {real_views}".ljust(45) + Fore.CYAN + "║")
        
        print(Fore.CYAN + "╠" + "═" * 70 + "╣")
        
        # آمار اصلی
        print(Fore.CYAN + "║ " + Fore.GREEN + "✅ SUCCESS".ljust(15) + f": {successful_views:>10,}".ljust(15) + 
              Fore.CYAN + "│" + Fore.YELLOW + " 🔄 TOTAL".ljust(15) + f": {total_views_sent:>10,}".ljust(14) + Fore.CYAN + "║")
        print(Fore.CYAN + "║ " + Fore.RED + "❌ PROXY ERR".ljust(15) + f": {proxy_errors:>10,}".ljust(15) + 
              Fore.CYAN + "│" + Fore.RED + " ⚠️ TOKEN ERR".ljust(15) + f": {token_errors:>10,}".ljust(14) + Fore.CYAN + "║")
        
        print(Fore.CYAN + "╠" + "═" * 70 + "╣")
        
        # سرعت
        print(Fore.CYAN + "║ " + Fore.MAGENTA + "⚡ SPEED".ljust(12) + f": {current_speed:>6.2f}/s".ljust(20) + 
              Fore.CYAN + "│" + Fore.BLUE + " 📊 SUCCESS RATE".ljust(18) + f": {success_rate:>5.1f}%".ljust(12) + Fore.CYAN + "║")
        print(Fore.CYAN + "║ " + Fore.WHITE + "⏱️  RUNTIME".ljust(12) + f": {hours:02d}:{minutes:02d}:{seconds:02d}".ljust(20) + 
              Fore.CYAN + "│" + Fore.WHITE + " 🧵 THREADS".ljust(18) + f": {active_count():>4,}/{THREADS}".ljust(12) + Fore.CYAN + "║")
        
        print(Fore.CYAN + "╠" + "═" * 70 + "╣")
        
        # پروکسی‌ها
        print(Fore.CYAN + "║ " + Fore.CYAN + "🌐 PROXY DISTRIBUTION:" + " " * 44 + "║")
        print(Fore.CYAN + "║ " + Fore.WHITE + "HTTP".ljust(8) + f": [{progress_bar(len(http_proxies), max_proxies_per_type)}] " + 
              f"{len(http_proxies):>4,}/{max_proxies_per_type}".ljust(36) + Fore.CYAN + "║")
        print(Fore.CYAN + "║ " + Fore.WHITE + "SOCKS4".ljust(8) + f": [{progress_bar(len(socks4_proxies), max_proxies_per_type)}] " + 
              f"{len(socks4_proxies):>4,}/{max_proxies_per_type}".ljust(36) + Fore.CYAN + "║")
        print(Fore.CYAN + "║ " + Fore.WHITE + "SOCKS5".ljust(8) + f": [{progress_bar(len(socks5_proxies), max_proxies_per_type)}] " + 
              f"{len(socks5_proxies):>4,}/{max_proxies_per_type}".ljust(36) + Fore.CYAN + "║")
        print(Fore.CYAN + "║ " + Fore.YELLOW + "TOTAL".ljust(8) + f": {total_proxies:>4,} proxies".ljust(48) + Fore.CYAN + "║")
        
        print(Fore.CYAN + "╠" + "═" * 70 + "╣")
        
        # سیستم
        print(Fore.CYAN + "║ " + Fore.CYAN + "💻 SYSTEM RESOURCES:" + " " * 46 + "║")
        print(Fore.CYAN + "║ " + Fore.WHITE + "CPU".ljust(8) + f": [{progress_bar(cpu, 100)}] {cpu:>5.1f}%".ljust(43) + Fore.CYAN + "║")
        print(Fore.CYAN + "║ " + Fore.WHITE + "RAM".ljust(8) + f": [{progress_bar(memory, 100)}] {memory:>5.1f}%".ljust(43) + Fore.CYAN + "║")
        
        print(Fore.CYAN + "╚" + "═" * 70 + "╝")
        
        # وضعیت
        if current_speed > 20:
            print(Fore.RED + "🚀 MODE: INSANE SPEED ACTIVATED! 🔥")
        elif current_speed > 10:
            print(Fore.MAGENTA + "⚡ MODE: TURBO CHARGED!")
        elif current_speed > 5:
            print(Fore.BLUE + "🔋 MODE: OPTIMAL PERFORMANCE")
        elif current_speed > 0:
            print(Fore.YELLOW + "⏳ MODE: NORMAL OPERATION")
        else:
            print(Fore.CYAN + "📡 MODE: COLLECTING PROXIES...")
        
        # آخرین User-Agent
        print(Fore.WHITE + f"🔄 Last UA: {get_ua()[:50]}...")
        
        sleep(1.5)

# ==================== شروع اصلی ====================

def main():
    global channel, post
    
    # لوگوی خوش‌آمدگویی
    print(Fore.CYAN + """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     🔥 TELEGRAM VIEW BOT - ULTIMATE EDITION 2026 🔥        ║
║                                                              ║
║        ✨ Professional View Bot with Auto Proxy ✨          ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║  • Auto Proxy Collection & Validation                       ║
║  • Smart Proxy Scoring System                               ║
║  • Real-time Statistics                                     ║
║  • Multi-threading Support                                  ║
║  • Random User-Agent                                        ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    # گرفتن لینک
    url = input(Fore.YELLOW + "📌 Enter Telegram post URL: " + Fore.WHITE).strip()
    
    try:
        channel, post = url.replace('https://t.me/', '').split('/')
        post = int(post)
    except:
        print(Fore.RED + "❌ Invalid URL! Use format: https://t.me/channel/123")
        return
    
    print(Fore.GREEN + f"\n✅ Target set: {channel}/{post}")
    print(Fore.CYAN + "📡 Collecting proxies...")
    
    # جمع‌آوری اولیه پروکسی
    start_scrap()
    
    print(Fore.GREEN + f"✅ Collected: HTTP:{len(http_proxies)} SOCKS4:{len(socks4_proxies)} SOCKS5:{len(socks5_proxies)}")
    print(Fore.YELLOW + "🚀 Starting workers...")
    
    # شروع همه تردها
    Thread(target=start_workers, daemon=True).start()
    Thread(target=check_views, daemon=True).start()
    Thread(target=auto_update_proxies, daemon=True).start()
    
    # نمایش آمار
    display_stats()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(Fore.RED + "\n\n⚠️ Bot stopped by user")
        print(Fore.GREEN + f"📊 Final Statistics:")
        print(Fore.GREEN + f"   ✅ Successful Views: {successful_views:,}")
        print(Fore.GREEN + f"   🔄 Total Requests: {total_views_sent:,}")
        print(Fore.GREEN + f"   ⏱️  Runtime: {datetime.now() - start_time}")
        errors.close()
        sys.exit(0)
