#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import re
import time
import threading
from datetime import datetime
from configparser import ConfigParser

# ========== رنګونه (پښتو) ==========
شین = '\033[92m'
ژیړ = '\033[93m'
سور = '\033[91m'
نیلي = '\033[94m'
آبي = '\033[96m'
ارغواني = '\033[95m'
سپین = '\033[97m'
بیا = '\033[0m'
بولډ = '\033[1m'

# ========== چوکات ==========
پورته = f"{آبي}╔═══════════════════════════════════════════════════════════════════════╗{بیا}"
منځ = f"{آبي}║{بیا}"
لاندې = f"{آبي}╚═══════════════════════════════════════════════════════════════════════╝{بیا}"
جلا = f"{آبي}╟───────────────────────────────────────────────────────────────────────╢{بیا}"

# ========== کتابتونونه ==========
try:
    import requests
except:
    os.system('pip install requests > /dev/null 2>&1')
    import requests

# ========== لوګو ==========
def لوګو():
    os.system('clear')
    لو = f"""
{بولډ}{آبي}╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║        {شین}██╗ ██████╗ ██╗   ██╗ █████╗     ██╗   ██╗██╗██╗██╗{آبي}           ║
║        {شین}██║██╔═══██╗╚██╗ ██╔╝██╔══██╗    ██║   ██║██║██║██║{آبي}           ║
║        {شین}██║██║   ██║ ╚████╔╝ ███████║    ██║   ██║██║██║██║{آبي}           ║
║        {شین}██║██║   ██║  ╚██╔╝  ██╔══██║    ╚██╗ ██╔╝██║██║██║{آبي}           ║
║        {شین}██║╚██████╔╝   ██║   ██║  ██║     ╚████╔╝ ██║██║██║{آبي}           ║
║        {شین}╚═╝ ╚═════╝    ╚═╝   ╚═╝  ╚═╝      ╚═══╝  ╚═╝╚═╝╚═╝{آبي}           ║
║                                                                       ║
║                    {ژیړ}██╗   ██╗██╗███████╗██╗{آبي}                           ║
║                    {ژیړ}██║   ██║██║██╔════╝██║{آبي}                           ║
║                    {ژیړ}██║   ██║██║█████╗  ██║{آبي}                           ║
║                    {ژیړ}╚██╗ ██╔╝██║██╔══╝  ██║{آبي}                           ║
║                    {ژیړ} ╚████╔╝ ██║███████╗██║{آبي}                           ║
║                    {ژیړ}  ╚═══╝  ╚═╝╚══════╝╚═╝{آبي}                           ║
║                                                                       ║
║                 {شین}⚡ {بولړ}جویا ویو ۳.۰{بیا}{شین} ⚡{آبي}                           ║
╚═══════════════════════════════════════════════════════════════════════╝{بیا}
"""
    print(لو)

# ========== تنظیمات ==========
تارونه = 200
وخت = 15
کارن = 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36'

# ========== ریګکس ==========
الګو = re.compile(r"(?:^|\D)?(("+ r"(?:[1-9]|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"):" + (r"(?:\d|[1-9]\d{1,3}|[1-5]\d{4}|6[0-4]\d{3}"
                + r"|65[0-4]\d{2}|655[0-2]\d|6553[0-5])")
                + r")(?:\D|$)")

# ========== اصلي کلاس ==========
class جویا:
    def __init__(self):
        self.http = []
        self.socks4 = []
        self.socks5 = []
        
        # شمیرې
        self.ټول = 0
        self.فعال = 0
        self.لیږل = 0
        self.ناکام = 0
        self.خراب = 0
        self.خطا = 0
        self.اوسنی = "0"
        
        # معلومات
        self.چینل = ""
        self.شمېره = 0
        self.پیل = time.time()
        self.روان = True
        self.قفل = threading.Lock()
        
        # سرچینې
        self.http_سرچ = []
        self.socks4_سرچ = []
        self.socks5_سرچ = []
        
        # د خطا فایل
        self.غلطي = None
    
    def لوډ(self):
        """د config.ini لوستل"""
        if not os.path.exists('config.ini'):
            print(f"{سور}{منځ}  config.ini نشته!                         {لاندې}")
            return False
        
        try:
            cfg = ConfigParser()
            cfg.read('config.ini', encoding='utf-8')
            
            if 'HTTP' in cfg:
                سر = cfg['HTTP'].get('Sources', '').splitlines()
                self.http_سرچ = [s.strip() for s in سر if s.strip() and ';' not in s]
            
            if 'SOCKS4' in cfg:
                سر = cfg['SOCKS4'].get('Sources', '').splitlines()
                self.socks4_سرچ = [s.strip() for s in سر if s.strip() and ';' not in s]
            
            if 'SOCKS5' in cfg:
                سر = cfg['SOCKS5'].get('Sources', '').splitlines()
                self.socks5_سرچ = [s.strip() for s in سر if s.strip() and ';' not in s]
            
            print(f"{شین}{منځ}  config.ini وموندل شو                     {لاندې}")
            return True
            
        except:
            print(f"{سور}{منځ}  config.ini خراب دی                       {لاندې}")
            return False
    
    def راټول(self):
        """د پروکسیو راټولول"""
        self.غلطي = open('errors.txt', 'a+', encoding='utf-8')
        
        self.http.clear()
        self.socks4.clear()
        self.socks5.clear()
        
        print(f"{آبي}{پورته}")
        print(f"{منځ}  {بولډ}پروکسی راټولول...{بیا}                              {لاندې}")
        
        تارونه = []
        
        if self.http_سرچ:
            t = threading.Thread(target=self.فچ, args=(self.http_سرچ, 'HTTP', self.http))
            تارونه.append(t)
            t.start()
        
        if self.socks4_سرچ:
            t = threading.Thread(target=self.فچ, args=(self.socks4_سرچ, 'SOCKS4', self.socks4))
            تارونه.append(t)
            t.start()
        
        if self.socks5_سرچ:
            t = threading.Thread(target=self.فچ, args=(self.socks5_سرچ, 'SOCKS5', self.socks5))
            تارونه.append(t)
            t.start()
        
        for t in تارونه:
            t.join()
        
        self.ټول = len(self.http) + len(self.socks4) + len(self.socks5)
        
        print(f"{شین}{منځ}  ټول: {self.ټول} | HTTP: {len(self.http)} | S4: {len(self.socks4)} | S5: {len(self.socks5)}  {لاندې}")
        print(f"{آبي}{لاندې}")
    
    def فچ(self, سرچینې, ډول, لیست):
        """د یو ډول پروکسی راوړل"""
        for سر in سرچینې:
            try:
                ر = requests.get(سر, timeout=وخت)
                if ر.status_code == 200:
                    شم = 0
                    for م in الګو.finditer(ر.text):
                        لیست.append(م.group(1))
                        شم += 1
                    with self.قفل:
                        print(f"{شین}{منځ}  ✓ {ډول}: +{شم}                     {لاندې}")
            except:
                pass
    
    def توکن(self, پروکسی, ډول):
        """د توکن ترلاسه کول"""
        try:
            s = requests.Session()
            ر = s.get(
                f'https://t.me/{self.چینل}/{self.شمېره}',
                params={'embed': '1', 'mode': 'tme'},
                headers={'referer': f'https://t.me/{self.چینل}/{self.شمېره}', 'user-agent': کارن},
                proxies={'http': f'{ډول}://{پروکسی}', 'https': f'{ډول}://{پروکسی}'},
                timeout=وخت)
            
            ټ = re.search('data-view="([^"]+)', ر.text)
            return ټ.group(1) if ټ else None, s
        except:
            return None, None
    
    def لیږد(self, توکن, s, پروکسی, ډول):
        """ویو لیږل"""
        try:
            کوکی = s.cookies.get_dict()
            ر = s.get(
                'https://t.me/v/',
                params={'views': str(توکن)},
                cookies={'stel_dt': '-240', 'stel_web_auth': 'https://web.telegram.org/z/'},
                headers={'referer': f'https://t.me/{self.چینل}/{self.شمېره}?embed=1&mode=tme', 'user-agent': کارن},
                proxies={'http': f'{ډول}://{پروکسی}', 'https': f'{ډول}://{پروکسی}'},
                timeout=وخت)
            
            return ر.status_code == 200 and ر.text == 'true'
        except:
            return False
    
    def پروسس(self, پروکسی, ډول):
        """د یو پروکسی پروسس"""
        with self.قفل:
            self.فعال += 1
        
        توکن, s = self.توکن(پروکسی, ډول)
        
        if توکن:
            if self.لیږد(توکن, s, پروکسی, ډول):
                with self.قفل:
                    self.لیږل += 1
            else:
                with self.قفل:
                    self.ناکام += 1
        else:
            with self.قفل:
                self.خراب += 1
        
        with self.قفل:
            self.فعال -= 1
    
    def کتل(self):
        """د اوسنیو ویو کتل"""
        while self.روان:
            try:
                ر = requests.get(
                    f'https://t.me/{self.چینل}/{self.شمېره}',
                    params={'embed': '1', 'mode': 'tme'},
                    headers={'referer': f'https://t.me/{self.چینل}/{self.شمېره}', 'user-agent': کارن},
                    timeout=وخت)
                
                م = re.search('<span class="tgme_widget_message_views">([^<]+)', ر.text)
                if م:
                    self.اوسنی = م.group(1)
                time.sleep(2)
            except:
                time.sleep(2)
    
    def ښودل(self):
        """د شمیرو ښودل"""
        while self.روان:
            لوګو()
            
            ت = int(time.time() - self.پیل)
            س = ت // 3600
            د = (ت % 3600) // 60
            ث = ت % 60
            
            print(f"{آبي}{پورته}")
            print(f"{منځ}  {بولډ}چینل:{بیا} {شین}{self.چینل}{بیا}                       {لاندې}")
            print(f"{منځ}  {بولډ}شمېره:{بیا} {شین}{self.شمېره}{بیا}                       {لاندې}")
            print(f"{آبي}{جلا}")
            
            print(f"{منځ}  {بولډ}اوسنی ویو:{بیا} {شین}{self.اوسنی}{بیا}                  {لاندې}")
            print(f"{منځ}  {بولډ}لیږل شوي:{بیا} {شین}{self.لیږل}{بیا}                    {لاندې}")
            print(f"{منځ}  {بولډ}ناکامه:{بیا} {سور}{self.ناکام}{بیا}                      {لاندې}")
            print(f"{منځ}  {بولډ}خراب توکن:{بیا} {سور}{self.خراب}{بیا}                    {لاندې}")
            print(f"{منځ}  {بولډ}د پروکسی خطا:{بیا} {سور}{self.خطا}{بیا}                  {لاندې}")
            print(f"{آبي}{جلا}")
            
            print(f"{منځ}  {بولډ}ټول پروکسی:{بیا} {نیلي}{self.ټول}{بیا}                   {لاندې}")
            print(f"{منځ}  {بولډ}فعال:{بیا} {شین}{self.فعال}{بیا}                         {لاندې}")
            print(f"{منځ}  {بولډ}HTTP:{بیا} {آبي}{len(self.http)}{بیا}                      {لاندې}")
            print(f"{منځ}  {بولځ}SOCKS4:{بیا} {آبي}{len(self.socks4)}{بیا}                   {لاندې}")
            print(f"{منځ}  {بولډ}SOCKS5:{بیا} {آبي}{len(self.socks5)}{بیا}                   {لاندې}")
            print(f"{آبي}{جلا}")
            
            print(f"{منځ}  {بولډ}وخت:{بیا} {ژیړ}{س:02d}:{د:02d}:{ث:02d}{بیا}                       {لاندې}")
            print(f"{آبي}{لاندې}")
            print(f"{ژیړ}{منځ}  Ctrl+C بندول{بیا}                           {لاندې}")
            print(f"{آبي}{لاندې}")
            
            time.sleep(1)
    
    def کار(self):
        """اصلي کار"""
        while self.روان:
            self.راټول()
            
            if self.ټول == 0:
                time.sleep(10)
                continue
            
            تارونه = []
            
            for p in self.http[:50]:
                t = threading.Thread(target=self.پروسس, args=(p, 'http'))
                تارونه.append(t)
                while threading.active_count() > تارونه:
                    time.sleep(0.1)
                t.start()
            
            time.sleep(1)
            
            for p in self.socks4[:50]:
                t = threading.Thread(target=self.پروسس, args=(p, 'socks4'))
                تارونه.append(t)
                while threading.active_count() > تارونه:
                    time.sleep(0.1)
                t.start()
            
            time.sleep(1)
            
            for p in self.socks5[:50]:
                t = threading.Thread(target=self.پروسس, args=(p, 'socks5'))
                تارونه.append(t)
                while threading.active_count() > تارونه:
                    time.sleep(0.1)
                t.start()
            
            for t in تارونه:
                t.join()
    
    def چلول(self):
        """د بوټ چلول"""
        try:
            لوګو()
            
            if not self.لوډ():
                input(f"{ژیړ}{منځ}  Enter کېږئ...{بیا}                     {لاندې}")
                return
            
            لینک = input(f"{شین}{منځ}  لینک:{بیا} ")
            
            try:
                لینک = لینک.replace('https://t.me/', '').replace('t.me/', '')
                برخې = لینک.split('/')
                if len(برخې) >= 2:
                    self.چینل = برخې[0]
                    self.شمېره = برخې[1]
                else:
                    raise
            except:
                print(f"{سور}{منځ}  لینک خراب دی!{بیا}                     {لاندې}")
                print(f"{ژیړ}{منځ}  نمونه: channel/123{بیا}                {لاندې}")
                input(f"{ژیړ}{منځ}  Enter کېږئ...{بیا}                     {لاندې}")
                return
            
            print(f"{شین}{منځ}  چینل: {self.چینل} | شمېره: {self.شمېره}{بیا}        {لاندې}")
            print(f"{ژیړ}{منځ}  پیل... Ctrl+C بندول{بیا}                  {لاندې}")
            time.sleep(2)
            
            threading.Thread(target=self.ښودل, daemon=True).start()
            threading.Thread(target=self.کتل, daemon=True).start()
            threading.Thread(target=self.کار, daemon=True).join()
            
        except KeyboardInterrupt:
            self.روان = False
            print(f"\n{ژیړ}{منځ}  بند شو!{بیا}                           {لاندې}")
            print(f"{شین}{منځ}  لیږل شوي: {self.لیږل}{بیا}                    {لاندې}")

if __name__ == '__main__':
    ب = جویا()
    ب.چلول()
