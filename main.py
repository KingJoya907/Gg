#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import re
import time
import threading
from datetime import datetime
from configparser import ConfigParser

# ========== Colors ==========
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
CYAN = '\033[96m'
MAGENTA = '\033[95m'
WHITE = '\033[97m'
RESET = '\033[0m'
BOLD = '\033[1m'

# ========== Box ==========
TOP = f"{CYAN}╔═══════════════════════════════════════════════════════════════════════╗{RESET}"
MID = f"{CYAN}║{RESET}"
BOT = f"{CYAN}╚═══════════════════════════════════════════════════════════════════════╝{RESET}"
LINE = f"{CYAN}╟───────────────────────────────────────────────────────────────────────╢{RESET}"

# ========== Install Requirements ==========
try:
    import requests
except:
    os.system('pip install requests > /dev/null 2>&1')
    import requests

# ========== Logo ==========
def show_logo():
    os.system('clear')
    logo = f"""
{BOLD}{CYAN}╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║     {GREEN}██╗ ██████╗ ██╗   ██╗ █████╗     {BLUE}██╗   ██╗██╗██╗██╗{CYAN}           ║
║     {GREEN}██║██╔═══██╗╚██╗ ██╔╝██╔══██╗    {BLUE}██║   ██║██║██║██║{CYAN}           ║
║     {GREEN}██║██║   ██║ ╚████╔╝ ███████║    {BLUE}██║   ██║██║██║██║{CYAN}           ║
║     {GREEN}██║██║   ██║  ╚██╔╝  ██╔══██║    {BLUE}╚██╗ ██╔╝██║██║██║{CYAN}           ║
║     {GREEN}██║╚██████╔╝   ██║   ██║  ██║     {BLUE}╚████╔╝ ██║██║██║{CYAN}           ║
║     {GREEN}╚═╝ ╚═════╝    ╚═╝   ╚═╝  ╚═╝      {BLUE}╚═══╝  ╚═╝╚═╝╚═╝{CYAN}           ║
║                                                                       ║
║                       {YELLOW}███████╗██╗███████╗██╗{CYAN}                         ║
║                       {YELLOW}██╔════╝██║██╔════╝██║{CYAN}                         ║
║                       {YELLOW}█████╗  ██║█████╗  ██║{CYAN}                         ║
║                       {YELLOW}██╔══╝  ██║██╔══╝  ██║{CYAN}                         ║
║                       {YELLOW}███████╗██║███████╗██║{CYAN}                         ║
║                       {YELLOW}╚══════╝╚═╝╚══════╝╚═╝{CYAN}                         ║
║                                                                       ║
║                    {GREEN}⚡ {BOLD}JOYA VIEW v3.0{RESET}{GREEN} ⚡{CYAN}                     ║
╚═══════════════════════════════════════════════════════════════════════╝{RESET}
"""
    print(logo)

# ========== Settings ==========
MAX_THREADS = 200
TIMEOUT = 15
USER_AGENT = 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36'

# ========== Proxy Regex ==========
PROXY_REGEX = re.compile(r"(?:^|\D)?(("+ r"(?:[1-9]|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"):" + (r"(?:\d|[1-9]\d{1,3}|[1-5]\d{4}|6[0-4]\d{3}"
                + r"|65[0-4]\d{2}|655[0-2]\d|6553[0-5])")
                + r")(?:\D|$)")

# ========== Main Class ==========
class JoyaView:
    def __init__(self):
        self.http_proxies = []
        self.socks4_proxies = []
        self.socks5_proxies = []
        
        # Statistics
        self.total_proxies = 0
        self.active_proxies = 0
        self.views_sent = 0
        self.views_failed = 0
        self.bad_tokens = 0
        self.proxy_errors = 0
        self.current_views = "0"
        
        # Info
        self.channel = ""
        self.post_id = ""
        self.start_time = time.time()
        self.running = True
        self.lock = threading.Lock()
        
        # Sources
        self.http_sources = []
        self.socks4_sources = []
        self.socks5_sources = []
        
        # Error file
        self.error_file = None
    
    def load_config(self):
        """Load config.ini file"""
        if not os.path.exists('config.ini'):
            print(f"{RED}{MID}  config.ini not found!                      {BOT}")
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
            
            print(f"{GREEN}{MID}  config.ini loaded successfully             {BOT}")
            return True
            
        except:
            print(f"{RED}{MID}  config.ini is corrupted!                   {BOT}")
            return False
    
    def collect_proxies(self):
        """Collect proxies from all sources"""
        self.error_file = open('errors.txt', 'a+', encoding='utf-8')
        
        self.http_proxies.clear()
        self.socks4_proxies.clear()
        self.socks5_proxies.clear()
        
        print(f"{CYAN}{TOP}")
        print(f"{MID}  {BOLD}Collecting proxies...{RESET}                              {BOT}")
        
        threads = []
        
        if self.http_sources:
            t = threading.Thread(target=self.fetch, args=(self.http_sources, 'HTTP', self.http_proxies))
            threads.append(t)
            t.start()
        
        if self.socks4_sources:
            t = threading.Thread(target=self.fetch, args=(self.socks4_sources, 'SOCKS4', self.socks4_proxies))
            threads.append(t)
            t.start()
        
        if self.socks5_sources:
            t = threading.Thread(target=self.fetch, args=(self.socks5_sources, 'SOCKS5', self.socks5_proxies))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        self.total_proxies = len(self.http_proxies) + len(self.socks4_proxies) + len(self.socks5_proxies)
        
        print(f"{GREEN}{MID}  Total: {self.total_proxies} | HTTP: {len(self.http_proxies)} | S4: {len(self.socks4_proxies)} | S5: {len(self.socks5_proxies)}  {BOT}")
        print(f"{CYAN}{BOT}")
    
    def fetch(self, sources, ptype, plist):
        """Fetch proxies from sources"""
        for src in sources:
            try:
                r = requests.get(src, timeout=TIMEOUT)
                if r.status_code == 200:
                    count = 0
                    for m in PROXY_REGEX.finditer(r.text):
                        plist.append(m.group(1))
                        count += 1
                    with self.lock:
                        print(f"{GREEN}{MID}  ✓ {ptype}: +{count} proxies                {BOT}")
            except:
                pass
    
    def get_token(self, proxy, ptype):
        """Get view token"""
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
        """Send view"""
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
    
    def process_proxy(self, proxy, ptype):
        """Process single proxy"""
        with self.lock:
            self.active_proxies += 1
        
        token, session = self.get_token(proxy, ptype)
        
        if token:
            if self.send_view(token, session, proxy, ptype):
                with self.lock:
                    self.views_sent += 1
            else:
                with self.lock:
                    self.views_failed += 1
        else:
            with self.lock:
                self.bad_tokens += 1
        
        with self.lock:
            self.active_proxies -= 1
    
    def check_current_views(self):
        """Check current view count"""
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
    
    def show_stats(self):
        """Display statistics"""
        while self.running:
            show_logo()
            
            elapsed = int(time.time() - self.start_time)
            h = elapsed // 3600
            m = (elapsed % 3600) // 60
            s = elapsed % 60
            
            print(f"{CYAN}{TOP}")
            print(f"{MID}  {BOLD}Channel:{RESET} {GREEN}{self.channel}{RESET}                       {BOT}")
            print(f"{MID}  {BOLD}Post ID:{RESET} {GREEN}{self.post_id}{RESET}                       {BOT}")
            print(f"{CYAN}{LINE}")
            
            print(f"{MID}  {BOLD}Current Views:{RESET} {GREEN}{self.current_views}{RESET}                  {BOT}")
            print(f"{MID}  {BOLD}Views Sent:{RESET} {GREEN}{self.views_sent}{RESET}                    {BOT}")
            print(f"{MID}  {BOLD}Failed Views:{RESET} {RED}{self.views_failed}{RESET}                    {BOT}")
            print(f"{MID}  {BOLD}Bad Tokens:{RESET} {RED}{self.bad_tokens}{RESET}                      {BOT}")
            print(f"{MID}  {BOLD}Proxy Errors:{RESET} {RED}{self.proxy_errors}{RESET}                   {BOT}")
            print(f"{CYAN}{LINE}")
            
            print(f"{MID}  {BOLD}Total Proxies:{RESET} {BLUE}{self.total_proxies}{RESET}                   {BOT}")
            print(f"{MID}  {BOLD}Active:{RESET} {GREEN}{self.active_proxies}{RESET}                         {BOT}")
            print(f"{MID}  {BOLD}HTTP:{RESET} {CYAN}{len(self.http_proxies)}{RESET}                        {BOT}")
            print(f"{MID}  {BOLD}SOCKS4:{RESET} {CYAN}{len(self.socks4_proxies)}{RESET}                     {BOT}")
            print(f"{MID}  {BOLD}SOCKS5:{RESET} {CYAN}{len(self.socks5_proxies)}{RESET}                     {BOT}")
            print(f"{CYAN}{LINE}")
            
            print(f"{MID}  {BOLD}Runtime:{RESET} {YELLOW}{h:02d}:{m:02d}:{s:02d}{RESET}                       {BOT}")
            print(f"{CYAN}{BOT}")
            print(f"{YELLOW}{MID}  Press Ctrl+C to stop{RESET}                           {BOT}")
            print(f"{CYAN}{BOT}")
            
            time.sleep(1)
    
    def worker(self):
        """Main worker thread"""
        while self.running:
            self.collect_proxies()
            
            if self.total_proxies == 0:
                time.sleep(10)
                continue
            
            threads = []
            
            for p in self.http_proxies[:50]:
                t = threading.Thread(target=self.process_proxy, args=(p, 'http'))
                threads.append(t)
                while threading.active_count() > MAX_THREADS:
                    time.sleep(0.1)
                t.start()
            
            time.sleep(1)
            
            for p in self.socks4_proxies[:50]:
                t = threading.Thread(target=self.process_proxy, args=(p, 'socks4'))
                threads.append(t)
                while threading.active_count() > MAX_THREADS:
                    time.sleep(0.1)
                t.start()
            
            time.sleep(1)
            
            for p in self.socks5_proxies[:50]:
                t = threading.Thread(target=self.process_proxy, args=(p, 'socks5'))
                threads.append(t)
                while threading.active_count() > MAX_THREADS:
                    time.sleep(0.1)
                t.start()
            
            for t in threads:
                t.join()
    
    def run(self):
        """Run the bot"""
        try:
            show_logo()
            
            if not self.load_config():
                input(f"{YELLOW}{MID}  Press Enter to exit...{RESET}                     {BOT}")
                return
            
            url = input(f"{GREEN}{MID}  Enter post URL:{RESET} ")
            
            try:
                url = url.replace('https://t.me/', '').replace('t.me/', '')
                parts = url.split('/')
                if len(parts) >= 2:
                    self.channel = parts[0]
                    self.post_id = parts[1]
                else:
                    raise
            except:
                print(f"{RED}{MID}  Invalid URL!{RESET}                           {BOT}")
                print(f"{YELLOW}{MID}  Example: channel/123{RESET}                    {BOT}")
                input(f"{YELLOW}{MID}  Press Enter to exit...{RESET}                     {BOT}")
                return
            
            print(f"{GREEN}{MID}  Channel: {self.channel} | Post: {self.post_id}{RESET}           {BOT}")
            print(f"{YELLOW}{MID}  Starting... Press Ctrl+C to stop{RESET}            {BOT}")
            time.sleep(2)
            
            threading.Thread(target=self.show_stats, daemon=True).start()
            threading.Thread(target=self.check_current_views, daemon=True).start()
            threading.Thread(target=self.worker, daemon=True).join()
            
        except KeyboardInterrupt:
            self.running = False
            print(f"\n{YELLOW}{MID}  Stopped!{RESET}                               {BOT}")
            print(f"{GREEN}{MID}  Views Sent: {self.views_sent}{RESET}                    {BOT}")

if __name__ == '__main__':
    bot = JoyaView()
    bot.run()
