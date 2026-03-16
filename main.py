#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Telegram View Bot 2026 - Final Termux Edition
Fully Optimized with config.ini Support
"""

import os
import sys
import re
import time
import json
import random
import threading
from datetime import datetime
from collections import deque
from configparser import ConfigParser

# Auto install dependencies
def install_dependencies():
    required = {
        'requests': 'requests',
        'socks': 'pysocks',
        'cloudscraper': 'cloudscraper',
        'fake_headers': 'fake-headers'
    }
    
    for module, package in required.items():
        try:
            __import__(module)
        except ImportError:
            os.system(f'pip install {package} --quiet')
            print(f"✅ {package} installed")

install_dependencies()

import requests
import cloudscraper
from fake_headers import Headers

# ==================== Configuration ====================
class Config:
    # General settings
    MAX_THREADS = 250
    REQUEST_TIMEOUT = 15
    RETRY_COUNT = 3
    REQUEST_DELAY = 0.3
    PROXY_TIMEOUT = 8
    PROXY_TEST_URL = 'http://httpbin.org/ip'
    
    # User Agents 2026
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0'
    ]

# ==================== Config Manager ====================
class ConfigManager:
    def __init__(self, config_file='config.ini'):
        self.config_file = config_file
        self.config = ConfigParser(interpolation=None)
        self.proxy_sources = {
            'http': [],
            'socks4': [],
            'socks5': []
        }
        self.load_config()
        
    def load_config(self):
        """Load configuration from config.ini"""
        if not os.path.exists(self.config_file):
            self.create_default_config()
            
        self.config.read(self.config_file, encoding='utf-8')
        
        # Load proxy sources
        for proxy_type in ['HTTP', 'SOCKS4', 'SOCKS5']:
            if proxy_type in self.config:
                sources = self.config[proxy_type].get('Sources', '').splitlines()
                # Clean and filter empty lines
                sources = [s.strip() for s in sources if s.strip() and not s.strip().startswith(';')]
                self.proxy_sources[proxy_type.lower()] = sources
                
        print(f"✅ Loaded {sum(len(v) for v in self.proxy_sources.values())} proxy sources")
        
    def create_default_config(self):
        """Create default config.ini file"""
        default_config = '''[HTTP]
Sources =
    https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/protocols/http/data.txt
    https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/http/data.txt
    https://raw.githubusercontent.com/komutan234/Proxy-List-Free/main/proxies/http.txt
    https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt
    https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/http.txt
    https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all
    https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt
    https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt
    https://openproxylist.xyz/http.txt
    https://proxyspace.pro/http.txt

[SOCKS4]
Sources =
    https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/protocols/socks4/data.txt
    https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/socks4/data.txt
    https://raw.githubusercontent.com/komutan234/Proxy-List-Free/main/proxies/socks4.txt
    https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks4.txt
    https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/socks4.txt
    https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks4&timeout=10000&country=all
    https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks4.txt
    https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks4.txt
    https://openproxylist.xyz/socks4.txt

[SOCKS5]
Sources =
    https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/protocols/socks5/data.txt
    https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/socks5/data.txt
    https://raw.githubusercontent.com/komutan234/Proxy-List-Free/main/proxies/socks5.txt
    https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt
    https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/socks5.txt
    https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks5&timeout=10000&country=all
    https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks5.txt
    https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks5.txt
    https://openproxylist.xyz/socks5.txt
    https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt
'''
        with open(self.config_file, 'w', encoding='utf-8') as f:
            f.write(default_config)
        print("✅ Created default config.ini")

# ==================== Proxy Manager ====================
class ProxyManager:
    def __init__(self, config_manager):
        self.config = config_manager
        self.proxies = {
            'http': deque(maxlen=2000),
            'socks4': deque(maxlen=2000),
            'socks5': deque(maxlen=2000)
        }
        self.bad_proxies = set()
        self.lock = threading.Lock()
        self.last_update = 0
        self.stats = {'total': 0, 'working': 0}
        
    def fetch_proxies(self, proxy_type):
        """Fetch proxies from sources"""
        all_proxies = []
        sources = self.config.proxy_sources.get(proxy_type, [])
        
        if not sources:
            return []
            
        print(f"\n📡 Fetching {proxy_type} proxies...")
        
        for url in sources:
            try:
                scraper = cloudscraper.create_scraper()
                response = scraper.get(url, timeout=Config.PROXY_TIMEOUT)
                
                if response.status_code == 200:
                    # Extract proxies
                    found = re.findall(r'\d+\.\d+\.\d+\.\d+:\d+', response.text)
                    
                    if found:
                        all_proxies.extend(found)
                        print(f"   → {len(found)} from {url.split('/')[2]}")
                        
            except Exception as e:
                continue
                
            time.sleep(0.5)
            
        # Remove duplicates
        all_proxies = list(set(all_proxies))
        
        # Quick test
        working = []
        test_sample = all_proxies[:100]  # Test first 100
        
        for proxy in test_sample:
            if self.test_proxy(proxy, proxy_type):
                working.append(proxy)
                
        print(f"   ✅ {len(working)} working {proxy_type} proxies found")
        
        return working
        
    def test_proxy(self, proxy, proxy_type):
        """Test if proxy is working"""
        try:
            if proxy_type == 'http':
                test_proxies = {
                    'http': f'http://{proxy}',
                    'https': f'http://{proxy}'
                }
            else:
                test_proxies = {
                    'http': f'{proxy_type}://{proxy}',
                    'https': f'{proxy_type}://{proxy}'
                }
                
            response = requests.get(
                Config.PROXY_TEST_URL,
                proxies=test_proxies,
                timeout=Config.PROXY_TIMEOUT
            )
            
            return response.status_code == 200
            
        except:
            return False
            
    def update_all(self):
        """Update all proxy types"""
        if time.time() - self.last_update < 120:  # Update every 2 minutes
            return
            
        print("\n" + "="*60)
        print("🔄 Updating proxies...")
        
        threads = []
        results = {}
        
        def update_type(proxy_type):
            working = self.fetch_proxies(proxy_type)
            with self.lock:
                for proxy in working:
                    if proxy not in self.bad_proxies:
                        self.proxies[proxy_type].append(proxy)
                results[proxy_type] = len(working)
                
        for proxy_type in ['http', 'socks4', 'socks5']:
            thread = threading.Thread(target=update_type, args=(proxy_type,))
            threads.append(thread)
            thread.start()
            time.sleep(0.2)
            
        for thread in threads:
            thread.join()
            
        self.last_update = time.time()
        
        # Update stats
        total = sum(len(p) for p in self.proxies.values())
        self.stats['total'] = total
        print(f"\n✅ Total working proxies: {total}")
        
    def get_proxy(self, preferred_type=None):
        """Get a proxy from the pool"""
        if preferred_type and self.proxies[preferred_type]:
            with self.lock:
                proxy = self.proxies[preferred_type].popleft()
                self.proxies[preferred_type].append(proxy)
                return proxy, preferred_type
                
        # Try random type
        types = ['http', 'socks5', 'socks4']
        random.shuffle(types)
        
        for proxy_type in types:
            if self.proxies[proxy_type]:
                with self.lock:
                    proxy = self.proxies[proxy_type].popleft()
                    self.proxies[proxy_type].append(proxy)
                    return proxy, proxy_type
                    
        return None, None
        
    def mark_bad(self, proxy, proxy_type):
        """Mark proxy as bad"""
        with self.lock:
            self.bad_proxies.add(proxy)
            if proxy in self.proxies[proxy_type]:
                self.proxies[proxy_type].remove(proxy)

# ==================== Main Bot Class ====================
class TelegramViewBot:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.proxy_manager = ProxyManager(self.config_manager)
        self.stats = {
            'sent': 0,
            'failed': 0,
            'total_views': 0,
            'start_time': time.time()
        }
        self.running = True
        self.channel = ''
        self.post = ''
        self.lock = threading.Lock()
        
        # Create logs directory
        os.makedirs('logs', exist_ok=True)
        
    def get_token(self, proxy, proxy_type):
        """Get view token with multiple methods"""
        headers = {
            'User-Agent': random.choice(Config.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        try:
            # Setup proxies
            if proxy_type == 'http':
                proxies = {
                    'http': f'http://{proxy}',
                    'https': f'http://{proxy}'
                }
            else:
                proxies = {
                    'http': f'{proxy_type}://{proxy}',
                    'https': f'{proxy_type}://{proxy}'
                }
                
            session = requests.Session()
            
            # Get main page
            url = f'https://t.me/{self.channel}/{self.post}'
            params = {
                'embed': '1',
                'mode': 'tme',
                'v': str(int(time.time()))
            }
            
            response = session.get(
                url,
                params=params,
                headers=headers,
                proxies=proxies,
                timeout=Config.REQUEST_TIMEOUT
            )
            
            # Try different token patterns
            token_patterns = [
                r'data-view="([^"]+)"',
                r'data-view-id="([^"]+)"',
                r'data-counter="([^"]+)"',
                r'"viewId":"([^"]+)"',
                r'data-view-key="([^"]+)"',
                r'data-view-token="([^"]+)"'
            ]
            
            for pattern in token_patterns:
                match = re.search(pattern, response.text)
                if match:
                    return match.group(1), session, proxies
                    
        except Exception as e:
            pass
            
        return None, None, None
        
    def send_view(self, token, session, proxies):
        """Send the view"""
        headers = {
            'User-Agent': random.choice(Config.USER_AGENTS),
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'X-Requested-With': 'XMLHttpRequest',
            'Connection': 'keep-alive',
            'Referer': f'https://t.me/{self.channel}/{self.post}?embed=1&mode=tme',
            'Origin': 'https://t.me'
        }
        
        try:
            response = session.get(
                'https://t.me/v/',
                params={'views': token},
                headers=headers,
                proxies=proxies,
                timeout=Config.REQUEST_TIMEOUT
            )
            
            # Check response
            if response.status_code == 200:
                text = response.text.strip().lower()
                if text in ['true', 'ok', '1', '"true"', '"ok"']:
                    return True
                    
        except:
            pass
            
        return False
        
    def worker(self):
        """Main worker thread"""
        while self.running:
            # Get a proxy
            proxy, proxy_type = self.proxy_manager.get_proxy()
            
            if not proxy:
                time.sleep(1)
                continue
                
            # Try to send view
            token, session, proxies = self.get_token(proxy, proxy_type)
            
            if not token:
                with self.lock:
                    self.stats['failed'] += 1
                    self.proxy_manager.mark_bad(proxy, proxy_type)
                continue
                
            success = self.send_view(token, session, proxies)
            
            with self.lock:
                if success:
                    self.stats['sent'] += 1
                else:
                    self.stats['failed'] += 1
                    self.proxy_manager.mark_bad(proxy, proxy_type)
                    
            time.sleep(Config.REQUEST_DELAY)
            
    def monitor_views(self):
        """Monitor real view count"""
        scraper = cloudscraper.create_scraper()
        
        while self.running:
            try:
                url = f'https://t.me/{self.channel}/{self.post}'
                headers = {'User-Agent': random.choice(Config.USER_AGENTS)}
                
                response = scraper.get(url, headers=headers, timeout=10)
                
                # Try different view patterns
                view_patterns = [
                    r'<span class="tgme_widget_message_views">([^<]+)',
                    r'data-view-counter="([^"]+)"',
                    r'"views":(\d+)',
                    r'<span class="views">([^<]+)',
                    r'data-post-views="([^"]+)"'
                ]
                
                for pattern in view_patterns:
                    match = re.search(pattern, response.text)
                    if match:
                        views = re.sub(r'[^\d]', '', match.group(1))
                        if views and views.isdigit():
                            with self.lock:
                                self.stats['total_views'] = int(views)
                            break
                            
            except Exception as e:
                pass
                
            time.sleep(3)
            
    def show_status(self):
        """Display status"""
        while self.running:
            os.system('clear')
            
            elapsed = int(time.time() - self.stats['start_time'])
            hours = elapsed // 3600
            minutes = (elapsed % 3600) // 60
            seconds = elapsed % 60
            
            speed = self.stats['sent'] / elapsed if elapsed > 0 else 0
            
            print("="*60)
            print("🤖 Telegram View Bot 2026 - Final Termux Edition")
            print("="*60)
            print(f"📌 Channel: {self.channel}")
            print(f"📌 Post: {self.post}")
            print("-"*60)
            print(f"✅ Views Sent: {self.stats['sent']:,}")
            print(f"❌ Failed: {self.stats['failed']:,}")
            print(f"👁️ Real Views: {self.stats['total_views']:,}")
            print(f"⚡ Speed: {speed:.1f} views/sec")
            print(f"⏱️ Runtime: {hours:02d}:{minutes:02d}:{seconds:02d}")
            print("-"*60)
            print("🔄 Proxy Status:")
            for ptype in ['http', 'socks4', 'socks5']:
                count = len(self.proxy_manager.proxies[ptype])
                bar = '█' * (count // 20) + '░' * (50 - (count // 20))
                print(f"   {ptype}: {count:4d} {bar}")
            print(f"   ⚠️ Bad: {len(self.proxy_manager.bad_proxies)}")
            print("="*60)
            print("🔥 Press Ctrl+C to stop")
            
            time.sleep(1)
            
    def proxy_updater(self):
        """Update proxies periodically"""
        while self.running:
            time.sleep(120)  # Update every 2 minutes
            self.proxy_manager.update_all()
            
    def run(self):
        """Main execution"""
        os.system('clear')
        
        print("="*60)
        print("Telegram View Bot 2026 - Final Termux Edition")
        print("="*60)
        
        # Get post URL
        url = input("\n📎 Enter Telegram post URL: ").strip()
        
        try:
            if 't.me/' in url:
                parts = url.split('t.me/')[-1].split('/')
                self.channel = parts[0]
                self.post = parts[1]
            else:
                self.channel, self.post = url.split('/')
        except:
            print("❌ Invalid URL!")
            return
            
        print(f"\n✅ Channel: {self.channel}")
        print(f"✅ Post: {self.post}")
        
        # Initial proxy update
        print("\n🔄 Fetching initial proxies...")
        self.proxy_manager.update_all()
        
        if sum(len(p) for p in self.proxy_manager.proxies.values()) == 0:
            print("❌ No proxies found! Check your internet connection.")
            return
            
        # Start threads
        threads = []
        
        # Worker threads
        print(f"\n🚀 Starting {Config.MAX_THREADS} workers...")
        for i in range(Config.MAX_THREADS):
            t = threading.Thread(target=self.worker, daemon=True)
            t.start()
            threads.append(t)
            if i % 50 == 0:
                time.sleep(0.1)
                
        # Monitor thread
        t = threading.Thread(target=self.monitor_views, daemon=True)
        t.start()
        threads.append(t)
        
        # Status thread
        t = threading.Thread(target=self.show_status, daemon=True)
        t.start()
        threads.append(t)
        
        # Proxy updater thread
        t = threading.Thread(target=self.proxy_updater, daemon=True)
        t.start()
        threads.append(t)
        
        # Keep running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping...")
            self.running = False
            time.sleep(2)
            
            # Save stats
            with open(f'logs/session_{int(time.time())}.json', 'w') as f:
                json.dump(self.stats, f)
            print("✅ Session stats saved")

# ==================== Main Entry ====================
if __name__ == "__main__":
    bot = TelegramViewBot()
    bot.run()
