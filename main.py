#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
██████╗  ██████╗ ██╗   ██╗ █████╗     ██╗   ██╗██╗███████╗██╗    ██╗
██╔══██╗██╔═══██╗╚██╗ ██╔╝██╔══██╗    ██║   ██║██║██╔════╝██║    ██║
██║  ██║██║   ██║ ╚████╔╝ ███████║    ██║   ██║██║█████╗  ██║ █╗ ██║
██║  ██║██║   ██║  ╚██╔╝  ██╔══██║    ╚██╗ ██╔╝██║██╔══╝  ██║███╗██║
██████╔╝╚██████╔╝   ██║   ██║  ██║     ╚████╔╝ ██║███████╗╚███╔███╔╝
╚═════╝  ╚═════╝    ╚═╝   ╚═╝  ╚═╝      ╚═══╝  ╚═╝╚══════╝ ╚══╝╚══╝ 
                                                                     
████████╗███████╗██╗     ███████╗ ██████╗ ██████╗  █████╗ ███╗   ███╗
╚══██╔══╝██╔════╝██║     ██╔════╝██╔════╝ ██╔══██╗██╔══██╗████╗ ████║
   ██║   █████╗  ██║     █████╗  ██║  ███╗██████╔╝███████║██╔████╔██║
   ██║   ██╔══╝  ██║     ██╔══╝  ██║   ██║██╔══██╗██╔══██║██║╚██╔╝██║
   ██║   ███████╗███████╗███████╗╚██████╔╝██║  ██║██║  ██║██║ ╚═╝ ██║
   ╚═╝   ╚══════╝╚══════╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝
                                                                     
                       جويا VIEW - د تلګرام ویو زیاتونکی
                       جوړونکی: @JoyaSoft | Version 3.0
"""

import os
import sys
import re
import time
import threading
from datetime import datetime
from configparser import ConfigParser
from collections import Counter

# رنګونه
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
CYAN = '\033[96m'
WHITE = '\033[97m'
MAGENTA = '\033[95m'
RESET = '\033[0m'
BOLD = '\033[1m'

# اړین کتابتونونه نصبول
try:
    import requests
except ImportError:
    print(f"{YELLOW}[INFO] Installing requests...{RESET}")
    os.system('pip install requests')
    import requests

# تنظیمات
THREADS = 300  # د تارونو شمیر
TIMEOUT = 15   # د وخت حد
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

# د proxy پیژندلو لپاره ریګکس
REGEX = re.compile(r"(?:^|\D)?(("+ r"(?:[1-9]|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"):" + (r"(?:\d|[1-9]\d{1,3}|[1-5]\d{4}|6[0-4]\d{3}"
                + r"|65[0-4]\d{2}|655[0-2]\d|6553[0-5])")
                + r")(?:\D|$)")

class TelegramViewBot:
    def __init__(self):
        self.http_proxies = []
        self.socks4_proxies = []
        self.socks5_proxies = []
        
        # د شمیرو لپاره متغیرونه
        self.total_proxies = 0
        self.active_proxies = 0
        self.views_sent = 0
        self.failed_views = 0
        self.bad_tokens = 0
        self.proxy_errors = 0
        self.current_views = "0"
        self.start_time = time.time()
        
        # د چینل معلومات
        self.channel = ""
        self.post = ""
        
        # د کنټرول لپاره
        self.running = True
        self.lock = threading.Lock()
        
        # د config سرچینې
        self.http_sources = []
        self.socks4_sources = []
        self.socks5_sources = []
        
        # د خطا فایل
        self.errors_file = None
        
    def clear_screen(self):
        """د سکرین پاکول"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_banner(self):
        """لوی لوګو"""
        banner = f"""
{BOLD}{CYAN}██████╗  ██████╗ ██╗   ██╗ █████╗     ██╗   ██╗██╗███████╗██╗    ██╗
██╔══██╗██╔═══██╗╚██╗ ██╔╝██╔══██╗    ██║   ██║██║██╔════╝██║    ██║
██║  ██║██║   ██║ ╚████╔╝ ███████║    ██║   ██║██║█████╗  ██║ █╗ ██║
██║  ██║██║   ██║  ╚██╔╝  ██╔══██║    ╚██╗ ██╔╝██║██╔══╝  ██║███╗██║
██████╔╝╚██████╔╝   ██║   ██║  ██║     ╚████╔╝ ██║███████╗╚███╔███╔╝
╚═════╝  ╚═════╝    ╚═╝   ╚═╝  ╚═╝      ╚═══╝  ╚═╝╚══════╝ ╚══╝╚══╝ {RESET}
                                                                     
{BOLD}{GREEN}████████╗███████╗██╗     ███████╗ ██████╗ ██████╗  █████╗ ███╗   ███╗
╚══██╔══╝██╔════╝██║     ██╔════╝██╔════╝ ██╔══██╗██╔══██╗████╗ ████║
   ██║   █████╗  ██║     █████╗  ██║  ███╗██████╔╝███████║██╔████╔██║
   ██║   ██╔══╝  ██║     ██╔══╝  ██║   ██║██╔══██╗██╔══██║██║╚██╔╝██║
   ██║   ███████╗███████╗███████╗╚██████╔╝██║  ██║██║  ██║██║ ╚═╝ ██║
   ╚═╝   ╚══════╝╚══════╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝{RESET}
                                                                     
{WHITE}═══════════════════════════════════════════════════════════════════════════
{BLUE}                     جويا VIEW - د تلګرام ویو زیاتونکی{RESET}
{WHITE}═══════════════════════════════════════════════════════════════════════════{RESET}
        """
        print(banner)
    
    def load_config(self):
        """د config.ini فایل لوستل"""
        if not os.path.exists('config.ini'):
            print(f"{RED}[✗] config.ini file not found!{RESET}")
            return False
        
        try:
            cfg = ConfigParser(interpolation=None)
            cfg.read("config.ini", encoding="utf-8")
            
            # HTTP سرچینې
            if "HTTP" in cfg:
                sources = cfg["HTTP"].get("Sources", "").splitlines()
                self.http_sources = [s.strip() for s in sources if s.strip() and not s.strip().startswith(';')]
            
            # SOCKS4 سرچینې
            if "SOCKS4" in cfg:
                sources = cfg["SOCKS4"].get("Sources", "").splitlines()
                self.socks4_sources = [s.strip() for s in sources if s.strip() and not s.strip().startswith(';')]
            
            # SOCKS5 سرچینې
            if "SOCKS5" in cfg:
                sources = cfg["SOCKS5"].get("Sources", "").splitlines()
                self.socks5_sources = [s.strip() for s in sources if s.strip() and not s.strip().startswith(';')]
            
            print(f"{GREEN}[✓] config.ini loaded successfully!{RESET}")
            print(f"{BLUE}    HTTP sources: {len(self.http_sources)}")
            print(f"    SOCKS4 sources: {len(self.socks4_sources)}")
            print(f"    SOCKS5 sources: {len(self.socks5_sources)}{RESET}")
            
            return True
            
        except Exception as e:
            print(f"{RED}[✗] Error loading config.ini: {e}{RESET}")
            return False
    
    def collect_proxies(self):
        """د ټولو پروکسیو راټولول"""
        self.errors_file = open('errors.txt', 'a+', encoding='utf-8')
        
        # لیستونه خالي کول
        self.http_proxies.clear()
        self.socks4_proxies.clear()
        self.socks5_proxies.clear()
        
        print(f"\n{BOLD}{CYAN}[*] Collecting proxies...{RESET}\n")
        
        threads = []
        
        # HTTP پروکسی
        if self.http_sources:
            t = threading.Thread(target=self._fetch_proxies, 
                               args=(self.http_sources, 'HTTP', self.http_proxies))
            threads.append(t)
            t.start()
        
        # SOCKS4 پروکسی
        if self.socks4_sources:
            t = threading.Thread(target=self._fetch_proxies, 
                               args=(self.socks4_sources, 'SOCKS4', self.socks4_proxies))
            threads.append(t)
            t.start()
        
        # SOCKS5 پروکسی
        if self.socks5_sources:
            t = threading.Thread(target=self._fetch_proxies, 
                               args=(self.socks5_sources, 'SOCKS5', self.socks5_proxies))
            threads.append(t)
            t.start()
        
        # د ټولو تارونو انتظار
        for t in threads:
            t.join()
        
        self.total_proxies = len(self.http_proxies) + len(self.socks4_proxies) + len(self.socks5_proxies)
        
        print(f"\n{GREEN}[✓] Total proxies collected: {self.total_proxies}{RESET}")
        print(f"{BLUE}    HTTP: {len(self.http_proxies)}")
        print(f"    SOCKS4: {len(self.socks4_proxies)}")
        print(f"    SOCKS5: {len(self.socks5_proxies)}{RESET}\n")
    
    def _fetch_proxies(self, sources, proxy_type, proxy_list):
        """د یو ډول پروکسی راټولول"""
        for source in sources:
            if not source:
                continue
            
            try:
                response = requests.get(source, timeout=TIMEOUT)
                
                if response.status_code == 200:
                    matches = REGEX.finditer(response.text)
                    count = 0
                    for match in matches:
                        proxy_list.append(match.group(1))
                        count += 1
                    
                    with self.lock:
                        print(f"{GREEN}  [✓] {proxy_type}: +{count} proxies{RESET}")
                else:
                    with self.lock:
                        print(f"{YELLOW}  [!] {proxy_type}: HTTP {response.status_code}{RESET}")
                    
            except Exception as e:
                with self.lock:
                    print(f"{RED}  [✗] {proxy_type}: Error{RESET}")
                if self.errors_file:
                    self.errors_file.write(f"{datetime.now()}: {str(e)}\n")
    
    def get_token(self, proxy, proxy_type):
        """د توکن ترلاسه کول"""
        try:
            session = requests.Session()
            
            response = session.get(
                f'https://t.me/{self.channel}/{self.post}',
                params={'embed': '1', 'mode': 'tme'},
                headers={
                    'referer': f'https://t.me/{self.channel}/{self.post}',
                    'user-agent': USER_AGENT
                },
                proxies={
                    'http': f'{proxy_type}://{proxy}',
                    'https': f'{proxy_type}://{proxy}'
                },
                timeout=TIMEOUT)
            
            match = re.search('data-view="([^"]+)', response.text)
            if match:
                return match.group(1), session
            return None, None
            
        except Exception:
            return None, None
    
    def send_view(self, token, session, proxy, proxy_type):
        """ویو لیږل"""
        try:
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
                    'referer': f'https://t.me/{self.channel}/{self.post}?embed=1&mode=tme',
                    'user-agent': USER_AGENT,
                    'x-requested-with': 'XMLHttpRequest'
                },
                proxies={
                    'http': f'{proxy_type}://{proxy}',
                    'https': f'{proxy_type}://{proxy}'
                },
                timeout=TIMEOUT)
            
            return response.status_code == 200 and response.text == 'true'
            
        except Exception:
            return False
    
    def process_proxy(self, proxy, proxy_type):
        """د یو پروکسی پروسس کول"""
        with self.lock:
            self.active_proxies += 1
        
        token, session = self.get_token(proxy, proxy_type)
        
        if token:
            success = self.send_view(token, session, proxy, proxy_type)
            if success:
                with self.lock:
                    self.views_sent += 1
                    print(f"{GREEN}  [✓] View sent! Total: {self.views_sent}{RESET}")
            else:
                with self.lock:
                    self.failed_views += 1
                    print(f"{YELLOW}  [!] View failed{RESET}")
        else:
            with self.lock:
                self.bad_tokens += 1
                print(f"{RED}  [✗] Bad token{RESET}")
        
        with self.lock:
            self.active_proxies -= 1
    
    def check_current_views(self):
        """د اوسني ویو شمیرل"""
        while self.running:
            try:
                response = requests.get(
                    f'https://t.me/{self.channel}/{self.post}',
                    params={'embed': '1', 'mode': 'tme'},
                    headers={
                        'referer': f'https://t.me/{self.channel}/{self.post}',
                        'user-agent': USER_AGENT
                    },
                    timeout=TIMEOUT)
                
                match = re.search('<span class="tgme_widget_message_views">([^<]+)', response.text)
                if match:
                    self.current_views = match.group(1)
                
                time.sleep(2)
                
            except Exception:
                time.sleep(2)
    
    def display_stats(self):
        """د شمیرو ښودل"""
        while self.running:
            self.clear_screen()
            self.print_banner()
            
            elapsed_time = int(time.time() - self.start_time)
            hours = elapsed_time // 3600
            minutes = (elapsed_time % 3600) // 60
            seconds = elapsed_time % 60
            
            print(f"{BOLD}{WHITE}Channel: {CYAN}{self.channel}{WHITE} | Post: {CYAN}{self.post}{RESET}")
            print(f"{WHITE}════════════════════════════════════════════════════════════════{RESET}\n")
            
            print(f"{BOLD}{WHITE}📊 Current Status:{RESET}")
            print(f"  {GREEN}✓ Current Views:{RESET}       {BOLD}{self.current_views}{RESET}")
            print(f"  {GREEN}✓ Views Sent:{RESET}         {BOLD}{self.views_sent}{RESET}")
            print(f"  {YELLOW}⚠ Failed Views:{RESET}       {BOLD}{self.failed_views}{RESET}")
            print(f"  {RED}✗ Bad Tokens:{RESET}         {BOLD}{self.bad_tokens}{RESET}")
            print(f"  {RED}✗ Proxy Errors:{RESET}       {BOLD}{self.proxy_errors}{RESET}\n")
            
            print(f"{BOLD}{WHITE}🌐 Proxy Status:{RESET}")
            print(f"  {BLUE}📦 Total Proxies:{RESET}      {BOLD}{self.total_proxies}{RESET}")
            print(f"  {GREEN}⚡ Active Proxies:{RESET}     {BOLD}{self.active_proxies}{RESET}")
            print(f"  {CYAN}🌍 HTTP:{RESET}              {BOLD}{len(self.http_proxies)}{RESET}")
            print(f"  {CYAN}🔰 SOCKS4:{RESET}            {BOLD}{len(self.socks4_proxies)}{RESET}")
            print(f"  {CYAN}🔰 SOCKS5:{RESET}            {BOLD}{len(self.socks5_proxies)}{RESET}\n")
            
            print(f"{BOLD}{WHITE}⏱ Runtime:{RESET}          {BOLD}{hours:02d}:{minutes:02d}:{seconds:02d}{RESET}")
            print(f"\n{CYAN}Press Ctrl+C to stop{RESET}")
            
            time.sleep(1)
    
    def worker(self):
        """اصلي کار کوونکی تار"""
        while self.running:
            # پروکسی راټولول
            self.collect_proxies()
            
            if self.total_proxies == 0:
                print(f"{RED}[✗] No proxies collected! Waiting 30 seconds...{RESET}")
                time.sleep(30)
                continue
            
            threads = []
            
            # د HTTP پروکسیو پروسس کول
            for proxy in self.http_proxies[:100]:  # محدودول
                t = threading.Thread(target=self.process_proxy, args=(proxy, 'http'))
                threads.append(t)
                
                while threading.active_count() > THREADS:
                    time.sleep(0.1)
                
                t.start()
            
            time.sleep(1)
            
            # د SOCKS4 پروکسیو پروسس کول
            for proxy in self.socks4_proxies[:100]:
                t = threading.Thread(target=self.process_proxy, args=(proxy, 'socks4'))
                threads.append(t)
                
                while threading.active_count() > THREADS:
                    time.sleep(0.1)
                
                t.start()
            
            time.sleep(1)
            
            # د SOCKS5 پروکسیو پروسس کول
            for proxy in self.socks5_proxies[:100]:
                t = threading.Thread(target=self.process_proxy, args=(proxy, 'socks5'))
                threads.append(t)
                
                while threading.active_count() > THREADS:
                    time.sleep(0.1)
                
                t.start()
            
            # د ټولو تارونو انتظار
            for t in threads:
                t.join()
    
    def run(self):
        """د بوټ چلول"""
        try:
            self.clear_screen()
            self.print_banner()
            
            # د config فایل لوستل
            if not self.load_config():
                input(f"\n{YELLOW}Press Enter to exit...{RESET}")
                return
            
            # د پوسټ لینک اخیستل
            url = input(f"\n{BOLD}{CYAN}📎 Enter Telegram post URL: {RESET}")
            
            try:
                url = url.replace('https://t.me/', '').replace('t.me/', '')
                parts = url.split('/')
                if len(parts) >= 2:
                    self.channel = parts[0]
                    self.post = parts[1]
                else:
                    raise ValueError("Invalid URL")
            except:
                print(f"{RED}[✗] Invalid URL format!{RESET}")
                print(f"{YELLOW}Example: https://t.me/channel/123{RESET}")
                input(f"\n{YELLOW}Press Enter to exit...{RESET}")
                return
            
            print(f"\n{GREEN}[✓] Channel: {self.channel}, Post: {self.post}{RESET}")
            print(f"{YELLOW}[!] Starting view bot... Press Ctrl+C to stop{RESET}")
            time.sleep(2)
            
            # د تارونو پیلول
            stats_thread = threading.Thread(target=self.display_stats, daemon=True)
            stats_thread.start()
            
            views_thread = threading.Thread(target=self.check_current_views, daemon=True)
            views_thread.start()
            
            worker_thread = threading.Thread(target=self.worker, daemon=True)
            worker_thread.start()
            
            # د تارونو انتظار
            worker_thread.join()
            
        except KeyboardInterrupt:
            print(f"\n\n{YELLOW}[!] Stopping...{RESET}")
        except Exception as e:
            print(f"{RED}[✗] Error: {e}{RESET}")
        finally:
            self.running = False
            if self.errors_file:
                self.errors_file.close()
            print(f"\n{GREEN}[✓] Bot stopped!{RESET}")
            print(f"{BLUE}    Views Sent: {self.views_sent}")
            print(f"    Failed Views: {self.failed_views}")
            print(f"    Bad Tokens: {self.bad_tokens}")
            print(f"    Proxy Errors: {self.proxy_errors}{RESET}")

if __name__ == "__main__":
    bot = TelegramViewBot()
    bot.run()
