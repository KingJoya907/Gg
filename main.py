#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# اړین کتابتونونه
import os
import re
import sys
import time
import threading
from datetime import datetime
from configparser import ConfigParser

# رنګونه (یوازې ASCII)
G = '\033[92m'  # شین
Y = '\033[93m'  # ژیړ
R = '\033[91m'  # سور
B = '\033[94m'  # نیلي
C = '\033[96m'  # آبي
M = '\033[95m'  # ارغواني
W = '\033[97m'  # سپین
X = '\033[0m'   # بیا رنګ
Z = '\033[1m'   # بولډ

# نصبول
try:
    import requests
except:
    os.system('pip install requests > /dev/null 2>&1')
    import requests

# ========== تنظیمات ==========
MAX_THREADS = 200
TIME_OUT = 15
USER_AGENT = 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36'

# ========== ریګکس ==========
REGEX = re.compile(r"(?:^|\D)?(("+ r"(?:[1-9]|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"):" + (r"(?:\d|[1-9]\d{1,3}|[1-5]\d{4}|6[0-4]\d{3}"
                + r"|65[0-4]\d{2}|655[0-2]\d|6553[0-5])")
                + r")(?:\D|$)")

class JoyaView:
    def __init__(self):
        self.http = []
        self.socks4 = []
        self.socks5 = []
        
        # شمیرې
        self.total = 0
        self.active = 0
        self.sent = 0
        self.failed = 0
        self.bad_token = 0
        self.proxy_error = 0
        self.current = "0"
        
        # معلومات
        self.channel = ""
        self.post = ""
        self.start = time.time()
        self.running = True
        self.lock = threading.Lock()
        
        # سرچینې
        self.http_src = []
        self.socks4_src = []
        self.socks5_src = []
        
    def clear(self):
        os.system('clear')
    
    def logo(self):
        لوگو = f"""
{Z}{C}    ╔══════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║        ██╗ ██████╗ ██╗   ██╗ █████╗     ██╗   ██╗██╗       ║
    ║        ██║██╔═══██╗╚██╗ ██╔╝██╔══██╗    ██║   ██║██║       ║
    ║        ██║██║   ██║ ╚████╔╝ ███████║    ██║   ██║██║       ║
    ║   ██   ██║██║   ██║  ╚██╔╝  ██╔══██║    ╚██╗ ██╔╝██║       ║
    ║   ╚█████╔╝╚██████╔╝   ██║   ██║  ██║     ╚████╔╝ ██║       ║
    ║    ╚════╝  ╚═════╝    ╚═╝   ╚═╝  ╚═╝      ╚═══╝  ╚═╝       ║
    ║                                                              ║
    ║        ██╗   ██╗██╗███████╗██╗    ██╗                      ║
    ║        ██║   ██║██║██╔════╝██║    ██║                      ║
    ║        ██║   ██║██║█████╗  ██║ █╗ ██║                      ║
    ║        ╚██╗ ██╔╝██║██╔══╝  ██║███╗██║                      ║
    ║         ╚████╔╝ ██║███████╗╚███╔███╔╝                      ║
    ║          ╚═══╝  ╚═╝╚══════╝ ╚══╝╚══╝                       ║
    ║                                                              ║
    ║                    {G}版本 3.0 - پښتو{C}                         ║
    ╚══════════════════════════════════════════════════════════════╝{X}
"""
        print(لوگو)
    
    بار = f"{C}    ╔══════════════════════════════════════════════════════════╗{X}"
    منځ = f"{C}    ║{X}"
    پای = f"{C}    ╚══════════════════════════════════════════════════════════╝{X}"
    
    def config(self):
        if not os.path.exists('config.ini'):
            print(f"{R}{self.منځ}  فایل config.ini نشته!                      {self.پای}")
            return False
        
        try:
            cfg = ConfigParser()
            cfg.read('config.ini', encoding='utf-8')
            
            if 'HTTP' in cfg:
                src = cfg['HTTP'].get('Sources', '').splitlines()
                self.http_src = [s.strip() for s in src if s.strip() and ';' not in s]
            
            if 'SOCKS4' in cfg:
                src = cfg['SOCKS4'].get('Sources', '').splitlines()
                self.socks4_src = [s.strip() for s in src if s.strip() and ';' not in s]
            
            if 'SOCKS5' in cfg:
                src = cfg['SOCKS5'].get('Sources', '').splitlines()
                self.socks5_src = [s.strip() for s in src if s.strip() and ';' not in s]
            
            print(f"{G}{self.منځ}  config.ini پیدا شو                         {self.پای}")
            return True
            
        except:
            print(f"{R}{self.منځ}  config.ini خراب دی!                       {self.پای}")
            return False
    
    راټولول(self):
        print(f"{C}{self.بار}")
        print(f"{self.منځ}  {Z}پروکسی راټولول...{X}                           {self.پای}")
        
        self.http.clear()
        self.socks4.clear()
        self.socks5.clear()
        
        تارونه = []
        
        if self.http_src:
            t = threading.Thread(target=self.فچ, args=(self.http_src, 'HTTP', self.http))
            تارونه.append(t)
            t.start()
        
        if self.socks4_src:
            t = threading.Thread(target=self.فچ, args=(self.socks4_src, 'SOCKS4', self.socks4))
            تارونه.append(t)
            t.start()
        
        if self.socks5_src:
            t = threading.Thread(target=self.فچ, args=(self.socks5_src, 'SOCKS5', self.socks5))
            تارونه.append(t)
            t.start()
        
        for t in تارونه:
            t.join()
        
        self.total = len(self.http) + len(self.socks4) + len(self.socks5)
        
        print(f"{G}{self.منځ}  ټول: {self.total} | HTTP: {len(self.http)} | S4: {len(self.socks4)} | S5: {len(self.socks5)}  {self.پای}")
    
    def فچ(self, سرچینې, ډول, لیست):
        for سرچینه in سرچینې:
            try:
                ر = requests.get(سرچینه, timeout=TIME_OUT)
                if ر.status_code == 200:
                    for م in REGEX.finditer(ر.text):
                        لیست.append(م.group(1))
            except:
                pass
    
    def توکن(self, پروکسی, ډول):
        try:
            s = requests.Session()
            ر = s.get(
                f'https://t.me/{self.channel}/{self.post}',
                params={'embed': '1', 'mode': 'tme'},
                headers={'referer': f'https://t.me/{self.channel}/{self.post}', 'user-agent': USER_AGENT},
                proxies={'http': f'{ډول}://{پروکسی}', 'https': f'{ډول}://{پروکسی}'},
                timeout=TIME_OUT)
            
            ټ = re.search('data-view="([^"]+)', ر.text)
            return ټ.group(1) if ټ else None, s
        except:
            return None, None
    
    def ویو(self, توکن, s, پروکسی, ډول):
        try:
            کوکی = s.cookies.get_dict()
            ر = s.get(
                'https://t.me/v/',
                params={'views': str(توکن)},
                cookies={'stel_dt': '-240', 'stel_web_auth': 'https://web.telegram.org/z/', 'stel_ssid': کوکی.get('stel_ssid')},
                headers={'referer': f'https://t.me/{self.channel}/{self.post}?embed=1&mode=tme', 'user-agent': USER_AGENT, 'x-requested-with': 'XMLHttpRequest'},
                proxies={'http': f'{ډول}://{پروکسی}', 'https': f'{ډول}://{پروکسی}'},
                timeout=TIME_OUT)
            
            return ر.status_code == 200 and ر.text == 'true'
        except:
            return False
    
    def پروسس(self, پروکسی, ډول):
        with self.lock:
            self.active += 1
        
        توکن, s = self.توکن(پروکسی, ډول)
        
        if توکن:
            if self.ویو(توکن, s, پروکسی, ډول):
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
    
    def ویوونه(self):
        while self.running:
            try:
                ر = requests.get(
                    f'https://t.me/{self.channel}/{self.post}',
                    params={'embed': '1', 'mode': 'tme'},
                    headers={'referer': f'https://t.me/{self.channel}/{self.post}', 'user-agent': USER_AGENT},
                    timeout=TIME_OUT)
                
                م = re.search('<span class="tgme_widget_message_views">([^<]+)', ر.text)
                if م:
                    self.current = م.group(1)
                time.sleep(2)
            except:
                time.sleep(2)
    
    ښودل(self):
        while self.running:
            self.clear()
            self.logo()
            
            وخت = int(time.time() - self.start)
            س = وخت // 3600
            د = (وخت % 3600) // 60
            ث = وخت % 60
            
            print(f"{C}{self.بار}")
            print(f"{self.منځ}  {Z}چینل:{X} {G}{self.channel}{X}                  {self.پای}")
            print(f"{self.منځ}  {Z}پوسټ:{X} {G}{self.post}{X}                    {self.پای}")
            print(f"{C}{self.بار}")
            
            print(f"{self.منځ}  {Z}اوسنی ویو:{X} {G}{self.current}{X}                {self.پای}")
            print(f"{self.منځ}  {Z}لیږل شوي:{X} {G}{self.sent}{X}                    {self.پای}")
            print(f"{self.منځ}  {Z}ناکامه:{X} {R}{self.failed}{X}                    {self.پای}")
            print(f"{self.منځ}  {Z}خراب توکن:{X} {R}{self.bad_token}{X}              {self.پای}")
            print(f"{self.منځ}  {Z}د پروکسی خطا:{X} {R}{self.proxy_error}{X}         {self.پای}")
            print(f"{C}{self.بار}")
            
            print(f"{self.منځ}  {Z}ټول پروکسی:{X} {B}{self.total}{X}                  {self.پای}")
            print(f"{self.منځ}  {Z}فعال:{X} {G}{self.active}{X}                       {self.پای}")
            print(f"{self.منځ}  {Z}HTTP:{X} {C}{len(self.http)}{X}                     {self.پای}")
            print(f"{self.منځ}  {Z}SOCKS4:{X} {C}{len(self.socks4)}{X}                 {self.پای}")
            print(f"{self.منځ}  {Z}SOCKS5:{X} {C}{len(self.socks5)}{X}                 {self.پای}")
            print(f"{C}{self.بار}")
            
            print(f"{self.منځ}  {Z}وخت:{X} {Y}{س:02d}:{د:02d}:{ث:02d}{X}                     {self.پای}")
            print(f"{C}{self.پای}")
            
            print(f"{Y}{self.منځ}  Ctrl+C بندول{X}                 {self.پای}")
            print(f"{C}{self.پای}")
            
            time.sleep(1)
    
    کار(self):
        while self.running:
            self.راټولول()
            
            if self.total == 0:
                time.sleep(10)
                continue
            
            تارونه = []
            
            for p in self.http[:50]:
                t = threading.Thread(target=self.پروسس, args=(p, 'http'))
                تارونه.append(t)
                while threading.active_count() > MAX_THREADS:
                    time.sleep(0.1)
                t.start()
            
            time.sleep(1)
            
            for p in self.socks4[:50]:
                t = threading.Thread(target=self.پروسس, args=(p, 'socks4'))
                تارونه.append(t)
                while threading.active_count() > MAX_THREADS:
                    time.sleep(0.1)
                t.start()
            
            time.sleep(1)
            
            for p in self.socks5[:50]:
                t = threading.Thread(target=self.پروسس, args=(p, 'socks5'))
                تارونه.append(t)
                while threading.active_count() > MAX_THREADS:
                    time.sleep(0.1)
                t.start()
            
            for t in تارونه:
                t.join()
    
    چلول(self):
        try:
            self.clear()
            self.logo()
            
            print(f"{C}{self.بار}")
            if not self.config():
                input(f"{Y}{self.منځ}  Enter کېږه...{X}                 {self.پای}")
                return
            print(f"{C}{self.پای}")
            
            لینک = input(f"{G}{self.منځ}  لینک:{X} ")
            
            try:
                لینک = لینک.replace('https://t.me/', '').replace('t.me/', '')
                برخې = لینک.split('/')
                if len(برخې) >= 2:
                    self.channel = برخې[0]
                    self.post = برخې[1]
                else:
                    raise
            except:
                print(f"{R}{self.منځ}  لینک خراب دی!{X}                   {self.پای}")
                print(f"{Y}{self.منځ}  نمونه: channel/123{X}              {self.پای}")
                input(f"{Y}{self.منځ}  Enter کېږه...{X}                 {self.پای}")
                return
            
            print(f"{C}{self.پای}")
            time.sleep(1)
            
            threading.Thread(target=self.ښودل, daemon=True).start()
            threading.Thread(target=self.ویوونه, daemon=True).start()
            threading.Thread(target=self.کار, daemon=True).join()
            
        except KeyboardInterrupt:
            self.running = False
            print(f"\n{Y}{self.منځ}  بند شو!{X}                         {self.پای}")
            print(f"{G}{self.منځ}  لیږل شوي: {self.sent}{X}                    {self.پای}")

if __name__ == '__main__':
    bot = JoyaView()
    bot.چلول()
