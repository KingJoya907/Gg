#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import re
import time
import threading
from datetime import datetime
from configparser import ConfigParser

# ========== رنگها (فارسی) ==========
سبز = '\033[92m'
زرد = '\033[93m'
قرمز = '\033[91m'
آبی = '\033[94m'
فیروزه = '\033[96m'
بنفش = '\033[95m'
سفید = '\033[97m'
پایان = '\033[0m'
پررنگ = '\033[1m'

# ========== کادر ==========
بالا = f"{فیروزه}╔═══════════════════════════════════════════════════════════════════════╗{پایان}"
وسط = f"{فیروزه}║{پایان}"
پایین = f"{فیروزه}╚═══════════════════════════════════════════════════════════════════════╝{پایان}"
خط = f"{فیروزه}╟───────────────────────────────────────────────────────────────────────╢{پایان}"

# ========== نصب کتابخانه ==========
try:
    import requests
except:
    os.system('pip install requests > /dev/null 2>&1')
    import requests

# ========== لوگوی بزرگ ==========
def لوگو():
    os.system('clear')
    طرح = f"""
{پررنگ}{فیروزه}╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║        {سبز}██╗ ██████╗ ██╗   ██╗ █████╗     ██╗   ██╗██╗██╗██╗{فیروزه}           ║
║        {سبز}██║██╔═══██╗╚██╗ ██╔╝██╔══██╗    ██║   ██║██║██║██║{فیروزه}           ║
║        {سبز}██║██║   ██║ ╚████╔╝ ███████║    ██║   ██║██║██║██║{فیروزه}           ║
║        {سبز}██║██║   ██║  ╚██╔╝  ██╔══██║    ╚██╗ ██╔╝██║██║██║{فیروزه}           ║
║        {سبز}██║╚██████╔╝   ██║   ██║  ██║     ╚████╔╝ ██║██║██║{فیروزه}           ║
║        {سبز}╚═╝ ╚═════╝    ╚═╝   ╚═╝  ╚═╝      ╚═══╝  ╚═╝╚═╝╚═╝{فیروزه}           ║
║                                                                       ║
║                    {زرد}██╗   ██╗██╗███████╗██╗{فیروزه}                           ║
║                    {زرد}██║   ██║██║██╔════╝██║{فیروزه}                           ║
║                    {زرد}██║   ██║██║█████╗  ██║{فیروزه}                           ║
║                    {زرد}╚██╗ ██╔╝██║██╔══╝  ██║{فیروزه}                           ║
║                    {زرد} ╚████╔╝ ██║███████╗██║{فیروزه}                           ║
║                    {زرد}  ╚═══╝  ╚═╝╚══════╝╚═╝{فیروزه}                           ║
║                                                                       ║
║                 {سبز}⚡ {پررنگ}جویا ویو ۳.۰{پایان}{سبز} ⚡{فیروزه}                           ║
╚═══════════════════════════════════════════════════════════════════════╝{پایان}
"""
    print(طرح)

# ========== تنظیمات ==========
تعداد_رشته = 200
زمان_تایم اوت = 15
کاربر = 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36'

# ========== الگوی پروکسی ==========
الگو = re.compile(r"(?:^|\D)?(("+ r"(?:[1-9]|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"):" + (r"(?:\d|[1-9]\d{1,3}|[1-5]\d{4}|6[0-4]\d{3}"
                + r"|65[0-4]\d{2}|655[0-2]\d|6553[0-5])")
                + r")(?:\D|$)")

# ========== کلاس اصلی ==========
class جویا:
    def __init__(self):
        self.http = []
        self.socks4 = []
        self.socks5 = []
        
        # آمار
        self.کل = 0
        self.فعال = 0
        self.ارسال = 0
        self.ناموفق = 0
        self.توکن_خراب = 0
        self.خطا = 0
        self.ویو_فعلی = "0"
        
        # اطلاعات
        self.کانال = ""
        self.شماره = 0
        self.شروع = time.time()
        self.درحال = True
        self.قفل = threading.Lock()
        
        # منابع
        self.http_منبع = []
        self.socks4_منبع = []
        self.socks5_منبع = []
        
        # فایل خطا
        self.خطاها = None
    
    def بارگذاری(self):
        """خواندن config.ini"""
        if not os.path.exists('config.ini'):
            print(f"{قرمز}{وسط}  فایل config.ini پیدا نشد!                 {پایین}")
            return False
        
        try:
            cfg = ConfigParser()
            cfg.read('config.ini', encoding='utf-8')
            
            if 'HTTP' in cfg:
                منبع = cfg['HTTP'].get('Sources', '').splitlines()
                self.http_منبع = [s.strip() for s in منبع if s.strip() and ';' not in s]
            
            if 'SOCKS4' in cfg:
                منبع = cfg['SOCKS4'].get('Sources', '').splitlines()
                self.socks4_منبع = [s.strip() for s in منبع if s.strip() and ';' not in s]
            
            if 'SOCKS5' in cfg:
                منبع = cfg['SOCKS5'].get('Sources', '').splitlines()
                self.socks5_منبع = [s.strip() for s in منبع if s.strip() and ';' not in s]
            
            print(f"{سبز}{وسط}  config.ini با موفقیت بارگذاری شد          {پایین}")
            return True
            
        except:
            print(f"{قرمز}{وسط}  config.ini خراب است!                      {پایین}")
            return False
    
    def جمع_آوری(self):
        """جمع آوری پروکسی ها"""
        self.خطاها = open('errors.txt', 'a+', encoding='utf-8')
        
        self.http.clear()
        self.socks4.clear()
        self.socks5.clear()
        
        print(f"{فیروزه}{بالا}")
        print(f"{وسط}  {پررنگ}در حال جمع آوری پروکسی...{پایان}                              {پایین}")
        
        رشته‌ها = []
        
        if self.http_منبع:
            t = threading.Thread(target=self.دریافت, args=(self.http_منبع, 'HTTP', self.http))
            رشته‌ها.append(t)
            t.start()
        
        if self.socks4_منبع:
            t = threading.Thread(target=self.دریافت, args=(self.socks4_منبع, 'SOCKS4', self.socks4))
            رشته‌ها.append(t)
            t.start()
        
        if self.socks5_منبع:
            t = threading.Thread(target=self.دریافت, args=(self.socks5_منبع, 'SOCKS5', self.socks5))
            رشته‌ها.append(t)
            t.start()
        
        for t in رشته‌ها:
            t.join()
        
        self.کل = len(self.http) + len(self.socks4) + len(self.socks5)
        
        print(f"{سبز}{وسط}  کل: {self.کل} | HTTP: {len(self.http)} | S4: {len(self.socks4)} | S5: {len(self.socks5)}  {پایین}")
        print(f"{فیروزه}{پایین}")
    
    def دریافت(self, منابع, نوع, لیست):
        """دریافت پروکسی از یک منبع"""
        for منبع in منابع:
            try:
                ر = requests.get(منبع, timeout=زمان_تایم اوت)
                if ر.status_code == 200:
                    تعداد = 0
                    for م in الگو.finditer(ر.text):
                        لیست.append(م.group(1))
                        تعداد += 1
                    with self.قفل:
                        print(f"{سبز}{وسط}  ✓ {نوع}: +{تعداد}                     {پایین}")
            except:
                pass
    
    def دریافت_توکن(self, پروکسی, نوع):
        """دریافت توکن"""
        try:
            نشست = requests.Session()
            پاسخ = نشست.get(
                f'https://t.me/{self.کانال}/{self.شماره}',
                params={'embed': '1', 'mode': 'tme'},
                headers={'referer': f'https://t.me/{self.کانال}/{self.شماره}', 'user-agent': کاربر},
                proxies={'http': f'{نوع}://{پروکسی}', 'https': f'{نوع}://{پروکسی}'},
                timeout=زمان_تایم اوت)
            
            توکن = re.search('data-view="([^"]+)', پاسخ.text)
            return توکن.group(1) if توکن else None, نشست
        except:
            return None, None
    
    def ارسال_ویو(self, توکن, نشست, پروکسی, نوع):
        """ارسال ویو"""
        try:
            کوکی = نشست.cookies.get_dict()
            پاسخ = نشست.get(
                'https://t.me/v/',
                params={'views': str(توکن)},
                cookies={'stel_dt': '-240', 'stel_web_auth': 'https://web.telegram.org/z/'},
                headers={'referer': f'https://t.me/{self.کانال}/{self.شماره}?embed=1&mode=tme', 'user-agent': کاربر},
                proxies={'http': f'{نوع}://{پروکسی}', 'https': f'{نوع}://{پروکسی}'},
                timeout=زمان_تایم اوت)
            
            return پاسخ.status_code == 200 and پاسخ.text == 'true'
        except:
            return False
    
    def پردازش(self, پروکسی, نوع):
        """پردازش یک پروکسی"""
        with self.قفل:
            self.فعال += 1
        
        توکن, نشست = self.دریافت_توکن(پروکسی, نوع)
        
        if توکن:
            if self.ارسال_ویو(توکن, نشست, پروکسی, نوع):
                with self.قفل:
                    self.ارسال += 1
            else:
                with self.قفل:
                    self.ناموفق += 1
        else:
            with self.قفل:
                self.توکن_خراب += 1
        
        with self.قفل:
            self.فعال -= 1
    
    def بررسی_ویو(self):
        """بررسی ویو فعلی"""
        while self.درحال:
            try:
                پاسخ = requests.get(
                    f'https://t.me/{self.کانال}/{self.شماره}',
                    params={'embed': '1', 'mode': 'tme'},
                    headers={'referer': f'https://t.me/{self.کانال}/{self.شماره}', 'user-agent': کاربر},
                    timeout=زمان_تایم اوت)
                
                ویو = re.search('<span class="tgme_widget_message_views">([^<]+)', پاسخ.text)
                if ویو:
                    self.ویو_فعلی = ویو.group(1)
                time.sleep(2)
            except:
                time.sleep(2)
    
    def نمایش(self):
        """نمایش آمار"""
        while self.درحال:
            لوگو()
            
            زمان = int(time.time() - self.شروع)
            ساعت = زمان // 3600
            دقیقه = (زمان % 3600) // 60
            ثانیه = زمان % 60
            
            print(f"{فیروزه}{بالا}")
            print(f"{وسط}  {پررنگ}کانال:{پایان} {سبز}{self.کانال}{پایان}                       {پایین}")
            print(f"{وسط}  {پررنگ}شماره:{پایان} {سبز}{self.شماره}{پایان}                       {پایین}")
            print(f"{فیروزه}{خط}")
            
            print(f"{وسط}  {پررنگ}ویو فعلی:{پایان} {سبز}{self.ویو_فعلی}{پایان}                  {پایین}")
            print(f"{وسط}  {پررنگ}ارسال شده:{پایان} {سبز}{self.ارسال}{پایان}                    {پایین}")
            print(f"{وسط}  {پررنگ}ناموفق:{پایان} {قرمز}{self.ناموفق}{پایان}                      {پایین}")
            print(f"{وسط}  {پررنگ}توکن خراب:{پایان} {قرمز}{self.توکن_خراب}{پایان}                {پایین}")
            print(f"{وسط}  {پررنگ}خطاهای پروکسی:{پایان} {قرمز}{self.خطا}{پایان}                  {پایین}")
            print(f"{فیروزه}{خط}")
            
            print(f"{وسط}  {پررنگ}کل پروکسی:{پایان} {آبی}{self.کل}{پایان}                       {پایین}")
            print(f"{وسط}  {پررنگ}فعال:{پایان} {سبز}{self.فعال}{پایان}                           {پایین}")
            print(f"{وسط}  {پررنگ}HTTP:{پایان} {فیروزه}{len(self.http)}{پایان}                      {پایین}")
            print(f"{وسط}  {پررنگ}SOCKS4:{پایان} {فیروزه}{len(self.socks4)}{پایان}                   {پایین}")
            print(f"{وسط}  {پررنگ}SOCKS5:{پایان} {فیروزه}{len(self.socks5)}{پایان}                   {پایین}")
            print(f"{فیروزه}{خط}")
            
            print(f"{وسط}  {پررنگ}زمان:{پایان} {زرد}{ساعت:02d}:{دقیقه:02d}:{ثانیه:02d}{پایان}                       {پایین}")
            print(f"{فیروزه}{پایین}")
            print(f"{زرد}{وسط}  Ctrl+C برای توقف{پایان}                           {پایین}")
            print(f"{فیروزه}{پایین}")
            
            time.sleep(1)
    
    def کارگر(self):
        """کارگر اصلی"""
        while self.درحال:
            self.جمع_آوری()
            
            if self.کل == 0:
                time.sleep(10)
                continue
            
            رشته‌ها = []
            
            for p in self.http[:50]:
                t = threading.Thread(target=self.پردازش, args=(p, 'http'))
                رشته‌ها.append(t)
                while threading.active_count() > تعداد_رشته:
                    time.sleep(0.1)
                t.start()
            
            time.sleep(1)
            
            for p in self.socks4[:50]:
                t = threading.Thread(target=self.پردازش, args=(p, 'socks4'))
                رشته‌ها.append(t)
                while threading.active_count() > تعداد_رشته:
                    time.sleep(0.1)
                t.start()
            
            time.sleep(1)
            
            for p in self.socks5[:50]:
                t = threading.Thread(target=self.پردازش, args=(p, 'socks5'))
                رشته‌ها.append(t)
                while threading.active_count() > تعداد_رشته:
                    time.sleep(0.1)
                t.start()
            
            for t in رشته‌ها:
                t.join()
    
    def اجرا(self):
        """اجرای ربات"""
        try:
            لوگو()
            
            if not self.بارگذاری():
                input(f"{زرد}{وسط}  اینتر را بزنید...{پایان}                     {پایین}")
                return
            
            لینک = input(f"{سبز}{وسط}  لینک پست:{پایان} ")
            
            try:
                لینک = لینک.replace('https://t.me/', '').replace('t.me/', '')
                بخش = لینک.split('/')
                if len(بخش) >= 2:
                    self.کانال = بخش[0]
                    self.شماره = بخش[1]
                else:
                    raise
            except:
                print(f"{قرمز}{وسط}  لینک اشتباه است!{پایان}                     {پایین}")
                print(f"{زرد}{وسط}  مثال: channel/123{پایان}                    {پایین}")
                input(f"{زرد}{وسط}  اینتر را بزنید...{پایان}                     {پایین}")
                return
            
            print(f"{سبز}{وسط}  کانال: {self.کانال} | شماره: {self.شماره}{پایان}        {پایین}")
            print(f"{زرد}{وسط}  شروع... Ctrl+C برای توقف{پایان}                  {پایین}")
            time.sleep(2)
            
            threading.Thread(target=self.نمایش, daemon=True).start()
            threading.Thread(target=self.بررسی_ویو, daemon=True).start()
            threading.Thread(target=self.کارگر, daemon=True).join()
            
        except KeyboardInterrupt:
            self.درحال = False
            print(f"\n{زرد}{وسط}  متوقف شد!{پایان}                           {پایین}")
            print(f"{سبز}{وسط}  ارسال شده: {self.ارسال}{پایان}                    {پایین}")

if __name__ == '__main__':
    ربات = جویا()
    ربات.اجرا()
