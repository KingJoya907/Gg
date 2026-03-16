#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import re
import time
import threading
from datetime import datetime
from configparser import ConfigParser

# ========== رنگها ==========
G = '\033[92m'  # سبز
Y = '\033[93m'  # زرد
R = '\033[91m'  # قرمز
B = '\033[94m'  # آبی
C = '\033[96m'  # فیروزه ای
M = '\033[95m'  # بنفش
W = '\033[97m'  # سفید
X = '\033[0m'   # پایان
Z = '\033[1m'   # پررنگ

# ========== کادر ==========
UP = f"{C}╔═══════════════════════════════════════════════════════════════════════╗{X}"
MD = f"{C}║{X}"
DN = f"{C}╚═══════════════════════════════════════════════════════════════════════╝{X}"
LN = f"{C}╟───────────────────────────────────────────────────────────────────────╢{X}"

# ========== نصب کتابخانه ==========
try:
    import requests
except:
    os.system('pip install requests > /dev/null 2>&1')
    import requests

# ========== لوگو ==========
def logo():
    os.system('clear')
    print(f"""
{Z}{C}╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║        {G}██╗ ██████╗ ██╗   ██╗ █████╗     ██╗   ██╗██╗██╗██╗{C}           ║
║        {G}██║██╔═══██╗╚██╗ ██╔╝██╔══██╗    ██║   ██║██║██║██║{C}           ║
║        {G}██║██║   ██║ ╚████╔╝ ███████║    ██║   ██║██║██║██║{C}           ║
║        {G}██║██║   ██║  ╚██╔╝  ██╔══██║    ╚██╗ ██╔╝██║██║██║{C}           ║
║        {G}██║╚██████╔╝   ██║   ██║  ██║     ╚████╔╝ ██║██║██║{C}           ║
║        {G}╚═╝ ╚═════╝    ╚═╝   ╚═╝  ╚═╝      ╚═══╝  ╚═╝╚═╝╚═╝{C}           ║
║                                                                       ║
║                    {Y}██╗   ██╗██╗███████╗██╗{C}                           ║
║                    {Y}██║   ██║██║██╔════╝██║{C}                           ║
║                    {Y}██║   ██║██║█████╗  ██║{C}                           ║
║                    {Y}╚██╗ ██╔╝██║██╔══╝  ██║{C}                           ║
║                    {Y} ╚████╔╝ ██║███████╗██║{C}                           ║
║                    {Y}  ╚═══╝  ╚═╝╚══════╝╚═╝{C}                           ║
║                                                                       ║
║                 {G}⚡ {Z}جویا ویو ۳.۰{X}{G} ⚡{C}                           ║
╚═══════════════════════════════════════════════════════════════════════╝{X}
""")

# ========== تنظیمات ==========
MAX_THREADS = 200
TIMEOUT = 15
USER_AGENT = 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36'

# ========== الگوی پروکسی ==========
PROXY_REGEX = re.compile(r"(?:^|\D)?(("+ r"(?:[1-9]|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"):" + (r"(?:\d|[1-9]\d{1,3}|[1-5]\d{4}|6[0-4]\d{3}"
                + r"|65[0-4]\d{2}|655[0-2]\d|6553[0-5])")
                + r")(?:\D|$)")

# ========== کلاس اصلی ==========
class JoyaView:
    def __init__(self):
        self.http_list = []
        self.socks4_list = []
        self.socks5_list = []
        
        # آمار
        self.total = 0
        self.active = 0
        self.sent = 0
        self.failed = 0
        self.bad_token = 0
        self.proxy_error = 0
        self.current_views = "0"
        
        # اطلاعات
        self.channel = ""
        self.post_id = ""
        self.start_time = time.time()
        self.running = True
        self.lock = threading.Lock()
        
        # منابع
        self.http_sources = []
        self.socks4_sources = []
        self.socks5_sources = []
        
        # فایل خطا
        self.error_file = None
    
    def load_config(self):
        """خواندن فایل config.ini"""
        if not os.path.exists('config.ini'):
            print(f"{R}{MD}  فایل config.ini پیدا نشد!                 {DN}")
            return False
        
        try:
            cfg = ConfigParser()
            cfg.read('config.ini', encoding='utf-8')
            
            if 'HTTP' in cfg:
                src = cfg['HTTP'].get('Sources', '').splitlines()
                self.http_sources = [s.strip() for s in src if s.strip() and ';' not in s]
            
            if 'SOCKS4' in cfg:
                src = cfg['SOCKS4'].get('Sources', '').splitlines()
                self.socks4_sources = [s.strip() for s in src if s.strip() and ';' not in s]
            
            if 'SOCKS5' in cfg:
                src = cfg['SOCKS5'].get('Sources', '').splitlines()
                self.socks5_sources = [s.strip() for s in src if s.strip() and ';' not in s]
            
            print(f"{G}{MD}  config.ini با موفقیت بارگذاری شد          {DN}")
            return True
            
        except:
            print(f"{R}{MD}  config.ini خراب است!                      {DN}")
            return False
    
    def collect_proxies(self):
        """جمع آوری پروکسی ها"""
        self.error_file = open('errors.txt', 'a+', encoding='utf-8')
        
        self.http_list.clear()
        self.socks4_list.clear()
        self.socks5_list.clear()
        
        print(f"{C}{UP}")
        print(f"{MD}  {Z}در حال جمع آوری پروکسی...{X}                              {DN}")
        
        threads = []
        
        if self.http_sources:
            t = threading.Thread(target=self.fetch, args=(self.http_sources, 'HTTP', self.http_list))
            threads.append(t)
            t.start()
        
        if self.socks4_sources:
            t = threading.Thread(target=self.fetch, args=(self.socks4_sources, 'SOCKS4', self.socks4_list))
            threads.append(t)
            t.start()
        
        if self.socks5_sources:
            t = threading.Thread(target=self.fetch, args=(self.socks5_sources, 'SOCKS5', self.socks5_list))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        self.total = len(self.http_list) + len(self.socks4_list) + len(self.socks5_list)
        
        print(f"{G}{MD}  کل: {self.total} | HTTP: {len(self.http_list)} | S4: {len(self.socks4_list)} | S5: {len(self.socks5_list)}  {DN}")
        print(f"{C}{DN}")
    
    def fetch(self, sources, ptype, plist):
        """دریافت پروکسی از منابع"""
        for src in sources:
            try:
                r = requests.get(src, timeout=TIMEOUT)
                if r.status_code == 200:
                    count = 0
                    for m in PROXY_REGEX.finditer(r.text):
                        plist.append(m.group(1))
                        count += 1
                    with self.lock:
                        print(f"{G}{MD}  ✓ {ptype}: +{count}                     {DN}")
            except:
                pass
    
    def get_token(self, proxy, ptype):
        """دریافت توکن"""
        try:
            session = requests.Session()
            r = session.get(
                f'https://t.me/{self.channel}/{self.post_id}',
                params={'embed': '1', 'mode': 'tme'},
                headers={'referer': f'https://t.me/{self.channel}/{self.post_id}', 'user-agent': USER_AGENT},
                proxies={'http': f'{ptype}://{proxy}', 'https': f'{ptype}://{proxy}'},
                timeout=TIMEOUT)
            
            token = re.search('data-view="([^"]+)', r.text)
            return token.group(1) if token else None, session
        except:
            return None, None
    
    def send_view(self, token, session, proxy, ptype):
        """ارسال ویو"""
        try:
            cookie = session.cookies.get_dict()
            r = session.get(
                'https://t.me/v/',
                params={'views': str(token)},
                cookies={'stel_dt': '-240', 'stel_web_auth': 'https://web.telegram.org/z/'},
                headers={'referer': f'https://t.me/{self.channel}/{self.post_id}?embed=1&mode=tme', 'user-agent': USER_AGENT},
                proxies={'http': f'{ptype}://{proxy}', 'https': f'{ptype}://{proxy}'},
                timeout=TIMEOUT)
            
            return r.status_code == 200 and r.text == 'true'
        except:
            return False
    
    def process(self, proxy, ptype):
        """پردازش یک پروکسی"""
        with self.lock:
            self.active += 1
        
        token, session = self.get_token(proxy, ptype)
        
        if token:
            if self.send_view(token, session, proxy, ptype):
                with self.lock:
                    self.sent += 1
            else:
                with self.lock:
                    self.failed += 1
        else:
            with self.lock:
                self.bad_token += 1
        
        with self.lock:
            self.active -= 1
    
    def check_views(self):
        """بررسی ویو فعلی"""
        while self.running:
            try:
                r = requests.get(
                    f'https://t.me/{self.channel}/{self.post_id}',
                    params={'embed': '1', 'mode': 'tme'},
                    headers={'referer': f'https://t.me/{self.channel}/{self.post_id}', 'user-agent': USER_AGENT},
                    timeout=TIMEOUT)
                
                views = re.search('<span class="tgme_widget_message_views">([^<]+)', r.text)
                if views:
                    self.current_views = views.group(1)
                time.sleep(2)
            except:
                time.sleep(2)
    
    def display(self):
        """نمایش آمار"""
        while self.running:
            logo()
            
            elapsed = int(time.time() - self.start_time)
            h = elapsed // 3600
            m = (elapsed % 3600) // 60
            s = elapsed % 60
            
            print(f"{C}{UP}")
            print(f"{MD}  {Z}کانال:{X} {G}{self.channel}{X}                       {DN}")
            print(f"{MD}  {Z}شماره:{X} {G}{self.post_id}{X}                       {DN}")
            print(f"{C}{LN}")
            
            print(f"{MD}  {Z}ویو فعلی:{X} {G}{self.current_views}{X}                  {DN}")
            print(f"{MD}  {Z}ارسال شده:{X} {G}{self.sent}{X}                    {DN}")
            print(f"{MD}  {Z}ناموفق:{X} {R}{self.failed}{X}                      {DN}")
            print(f"{MD}  {Z}توکن خراب:{X} {R}{self.bad_token}{X}                {DN}")
            print(f"{MD}  {Z}خطاهای پروکسی:{X} {R}{self.proxy_error}{X}          {DN}")
            print(f"{C}{LN}")
            
            print(f"{MD}  {Z}کل پروکسی:{X} {B}{self.total}{X}                       {DN}")
            print(f"{MD}  {Z}فعال:{X} {G}{self.active}{X}                           {DN}")
            print(f"{MD}  {Z}HTTP:{X} {C}{len(self.http_list)}{X}                      {DN}")
            print(f"{MD}  {Z}SOCKS4:{X} {C}{len(self.socks4_list)}{X}                   {DN}")
            print(f"{MD}  {Z}SOCKS5:{X} {C}{len(self.socks5_list)}{X}                   {DN}")
            print(f"{C}{LN}")
            
            print(f"{MD}  {Z}زمان:{X} {Y}{h:02d}:{m:02d}:{s:02d}{X}                       {DN}")
            print(f"{C}{DN}")
            print(f"{Y}{MD}  Ctrl+C برای توقف{X}                           {DN}")
            print(f"{C}{DN}")
            
            time.sleep(1)
    
    def worker(self):
        """کارگر اصلی"""
        while self.running:
            self.collect_proxies()
            
            if self.total == 0:
                time.sleep(10)
                continue
            
            threads = []
            
            for p in self.http_list[:50]:
                t = threading.Thread(target=self.process, args=(p, 'http'))
                threads.append(t)
                while threading.active_count() > MAX_THREADS:
                    time.sleep(0.1)
                t.start()
            
            time.sleep(1)
            
            for p in self.socks4_list[:50]:
                t = threading.Thread(target=self.process, args=(p, 'socks4'))
                threads.append(t)
                while threading.active_count() > MAX_THREADS:
                    time.sleep(0.1)
                t.start()
            
            time.sleep(1)
            
            for p in self.socks5_list[:50]:
                t = threading.Thread(target=self.process, args=(p, 'socks5'))
                threads.append(t)
                while threading.active_count() > MAX_THREADS:
                    time.sleep(0.1)
                t.start()
            
            for t in threads:
                t.join()
    
    def run(self):
        """اجرای ربات"""
        try:
            logo()
            
            if not self.load_config():
                input(f"{Y}{MD}  اینتر را بزنید...{X}                     {DN}")
                return
            
            link = input(f"{G}{MD}  لینک پست:{X} ")
            
            try:
                link = link.replace('https://t.me/', '').replace('t.me/', '')
                parts = link.split('/')
                if len(parts) >= 2:
                    self.channel = parts[0]
                    self.post_id = parts[1]
                else:
                    raise
            except:
                print(f"{R}{MD}  لینک اشتباه است!{X}                     {DN}")
                print(f"{Y}{MD}  مثال: channel/123{X}                    {DN}")
                input(f"{Y}{MD}  اینتر را بزنید...{X}                     {DN}")
                return
            
            print(f"{G}{MD}  کانال: {self.channel} | شماره: {self.post_id}{X}        {DN}")
            print(f"{Y}{MD}  شروع... Ctrl+C برای توقف{X}                  {DN}")
            time.sleep(2)
            
            threading.Thread(target=self.display, daemon=True).start()
            threading.Thread(target=self.check_views, daemon=True).start()
            threading.Thread(target=self.worker, daemon=True).join()
            
        except KeyboardInterrupt:
            self.running = False
            print(f"\n{Y}{MD}  متوقف شد!{X}                           {DN}")
            print(f"{G}{MD}  ارسال شده: {self.sent}{X}                    {DN}")

if __name__ == '__main__':
    bot = JoyaView()
    bot.run()
