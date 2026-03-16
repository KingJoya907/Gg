#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Telegram View Bot 2026 - Termux Optimized
Anti-block, High Performance, Socks5 Support
"""

import os
import sys
import re
import time
import json
import random
import threading
import socket
from datetime import datetime
from collections import deque
from urllib.parse import urlparse

# Auto install dependencies for Termux
def install_dependencies():
    required = {
        'requests': 'requests',
        'socks': 'pysocks',
        'fake_headers': 'fake-headers',
        'cloudscraper': 'cloudscraper'
    }
    
    for module, package in required.items():
        try:
            __import__(module)
        except ImportError:
            os.system(f'pip install {package} --quiet')
            print(f"✅ {package} installed")

install_dependencies()

import requests
import socks
import cloudscraper
from fake_headers import Headers

# ==================== Main Configuration ====================
class Config:
    # General settings
    MAX_THREADS = 300  # Lower for Termux
    REQUEST_TIMEOUT = 10
    RETRY_COUNT = 2
    REQUEST_DELAY = 0.3
    
    # Proxy settings
    PROXY_TIMEOUT = 5
    PROXY_TEST_URL = 'http://httpbin.org/ip'
    MAX_PROXY_AGE = 300  # seconds
    
    # New 2026 User Agents
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1'
    ]
    
    # New 2026 Proxy APIs
    PROXY_SOURCES = {
        'http': [
            'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=5000&country=all',
            'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
            'https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt',
            'https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt'
        ],
        'socks4': [
            'https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks4&timeout=5000&country=all',
            'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt',
            'https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt'
        ],
        'socks5': [
            'https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks5&timeout=5000&country=all',
            'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt',
            'https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt',
            'https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt'
        ]
    }

# ==================== Proxy Manager Class ====================
class ProxyManager:
    def __init__(self):
        self.proxies = {
            'http': deque(maxlen=1000),
            'socks4': deque(maxlen=1000),
            'socks5': deque(maxlen=1000)
        }
        self.bad_proxies = set()
        self.lock = threading.Lock()
        self.last_update = 0
        
    def fetch_proxies(self, proxy_type):
        """Fetch proxies from different sources"""
        proxies = []
        sources = Config.PROXY_SOURCES.get(proxy_type, [])
        
        for url in sources:
            try:
                scraper = cloudscraper.create_scraper()
                response = scraper.get(url, timeout=Config.PROXY_TIMEOUT)
                
                if response.status_code == 200:
                    # Extract proxies with regex
                    found = re.findall(r'\d+\.\d+\.\d+\.\d+:\d+', response.text)
                    
                    # Quick proxy testing
                    for proxy in found[:50]:  # Limit for speed
                        if self.test_proxy(proxy, proxy_type):
                            proxies.append(proxy)
                            
                    print(f"📡 {len(found)} {proxy_type} proxies fetched from {url}")
                    
            except Exception as e:
                continue
                
            time.sleep(1)
            
        return list(set(proxies))  # Remove duplicates
        
    def test_proxy(self, proxy, proxy_type):
        """Test proxy health"""
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
                'http://httpbin.org/ip',
                proxies=test_proxies,
                timeout=Config.PROXY_TIMEOUT
            )
            
            return response.status_code == 200
            
        except:
            return False
            
    def update_proxies(self):
        """Update proxy list"""
        if time.time() - self.last_update < 60:  # Update every 1 minute
            return
            
        print("\n🔄 Fetching new proxies...")
        
        threads = []
        for proxy_type in ['http', 'socks4', 'socks5']:
            thread = threading.Thread(
                target=self._update_type,
                args=(proxy_type,)
            )
            threads.append(thread)
            thread.start()
            time.sleep(0.5)
            
        for thread in threads:
            thread.join()
            
        self.last_update = time.time()
        
        # Show statistics
        total = sum(len(p) for p in self.proxies.values())
        print(f"\n✅ {total} working proxies ready")
        
    def _update_type(self, proxy_type):
        """Update specific proxy type"""
        new_proxies = self.fetch_proxies(proxy_type)
        
        with self.lock:
            for proxy in new_proxies:
                if proxy not in self.bad_proxies:
                    self.proxies[proxy_type].append(proxy)
                    
    def get_proxy(self, proxy_type='http'):
        """Get a proxy from the list"""
        with self.lock:
            if self.proxies[proxy_type]:
                proxy = self.proxies[proxy_type].popleft()
                self.proxies[proxy_type].append(proxy)  # Return to end of queue
                return proxy
        return None
        
    def mark_bad(self, proxy, proxy_type):
        """Mark proxy as bad"""
        with self.lock:
            self.bad_proxies.add(proxy)
            # Remove from main list
            if proxy in self.proxies[proxy_type]:
                self.proxies[proxy_type].remove(proxy)

# ==================== Main Bot Class ====================
class TelegramViewBot:
    def __init__(self):
        self.proxy_manager = ProxyManager()
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
        
        # Storage structure
        os.makedirs('logs', exist_ok=True)
        
    def log(self, msg, level='info'):
        """Log with timestamp"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {msg}")
        
    def get_token(self, proxy, proxy_type):
        """Get view token with 2026 method"""
        headers = {
            'User-Agent': random.choice(Config.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        try:
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
            
            # Step 1: Get main page
            url = f'https://t.me/{self.channel}/{self.post}'
            params = {
                'embed': '1',
                'mode': 'tme',
                'v': str(int(time.time()))  # Cache buster
            }
            
            response = session.get(
                url,
                params=params,
                headers=headers,
                proxies=proxies,
                timeout=Config.REQUEST_TIMEOUT
            )
            
            # Extract token using different methods
            token = None
            
            # Method 1: data-view
            match = re.search(r'data-view="([^"]+)"', response.text)
            if match:
                token = match.group(1)
                
            # Method 2: data-view-id
            if not token:
                match = re.search(r'data-view-id="([^"]+)"', response.text)
                if match:
                    token = match.group(1)
                    
            # Method 3: views counter
            if not token:
                match = re.search(r'data-counter="([^"]+)"', response.text)
                if match:
                    token = match.group(1)
                    
            if token:
                return token, session, proxies
                
        except Exception as e:
            pass
            
        return None, None, None
        
    def send_view(self, token, session, proxies):
        """Send view with new method"""
        headers = {
            'User-Agent': random.choice(Config.USER_AGENTS),
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.5',
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
                if response.text.strip() in ['true', 'ok', '1']:
                    return True
                    
        except:
            pass
            
        return False
        
    def worker(self, proxy_type='http'):
        """Main worker for sending views"""
        while self.running:
            proxy = self.proxy_manager.get_proxy(proxy_type)
            
            if not proxy:
                time.sleep(2)
                continue
                
            # Get token
            token, session, proxies = self.get_token(proxy, proxy_type)
            
            if not token:
                with self.lock:
                    self.stats['failed'] += 1
                    self.proxy_manager.mark_bad(proxy, proxy_type)
                continue
                
            # Send view
            success = self.send_view(token, session, proxies)
            
            with self.lock:
                if success:
                    self.stats['sent'] += 1
                else:
                    self.stats['failed'] += 1
                    self.proxy_manager.mark_bad(proxy, proxy_type)
                    
            time.sleep(Config.REQUEST_DELAY)
            
    def monitor_views(self):
        """Monitor view count"""
        scraper = cloudscraper.create_scraper()
        
        while self.running:
            try:
                url = f'https://t.me/{self.channel}/{self.post}'
                headers = {'User-Agent': random.choice(Config.USER_AGENTS)}
                
                response = scraper.get(url, headers=headers, timeout=10)
                
                # Extract view count
                patterns = [
                    r'<span class="tgme_widget_message_views">([^<]+)',
                    r'data-view-counter="([^"]+)"',
                    r'"views":(\d+)'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, response.text)
                    if match:
                        views = match.group(1).strip()
                        # Remove commas and extra characters
                        views = re.sub(r'[^\d]', '', views)
                        if views:
                            self.stats['total_views'] = int(views)
                            break
                            
            except:
                pass
                
            time.sleep(5)
            
    def show_status(self):
        """Show status display"""
        while self.running:
            elapsed = int(time.time() - self.stats['start_time'])
            hours = elapsed // 3600
            minutes = (elapsed % 3600) // 60
            seconds = elapsed % 60
            
            # Calculate speed
            if elapsed > 0:
                speed = self.stats['sent'] / elapsed
            else:
                speed = 0
                
            # Clear screen and show stats
            os.system('clear')
            
            print("="*60)
            print("🤖 Telegram View Bot 2026 - Termux Edition")
            print("="*60)
            print(f"📌 Channel: {self.channel}")
            print(f"📌 Post: {self.post}")
            print("-"*60)
            print(f"✅ Views Sent: {self.stats['sent']}")
            print(f"❌ Failed Views: {self.stats['failed']}")
            print(f"👁️ Current Views: {self.stats['total_views']:,}")
            print(f"⚡ Speed: {speed:.1f} views/sec")
            print(f"⏱️ Runtime: {hours:02d}:{minutes:02d}:{seconds:02d}")
            print("-"*60)
            print("🔄 Active Proxies:")
            for ptype in ['http', 'socks4', 'socks5']:
                count = len(self.proxy_manager.proxies[ptype])
                print(f"   {ptype}: {count}")
            print("="*60)
            print("🔥 Press Ctrl+C to stop")
            
            time.sleep(1)
            
    def run(self):
        """Main execution"""
        os.system('clear')
        
        print("="*60)
        print("Telegram View Bot 2026 - Termux Version")
        print("="*60)
        
        # Get link
        url = input("\n📎 Enter Telegram post URL: ").strip()
        
        try:
            if 't.me/' in url:
                parts = url.split('t.me/')[-1].split('/')
                self.channel = parts[0]
                self.post = parts[1]
            else:
                self.channel, self.post = url.split('/')
        except:
            print("❌ Invalid link!")
            return
            
        print(f"\n✅ Channel: {self.channel}")
        print(f"✅ Post: {self.post}")
        
        # Initial proxy update
        print("\n🔄 Fetching initial proxies...")
        self.proxy_manager.update_proxies()
        
        # Start threads
        threads = []
        
        # Proxy update thread
        update_thread = threading.Thread(target=self._proxy_updater, daemon=True)
        update_thread.start()
        threads.append(update_thread)
        
        # Worker threads
        for i in range(Config.MAX_THREADS):
            proxy_type = random.choice(['http', 'socks4', 'socks5'])
            worker = threading.Thread(
                target=self.worker,
                args=(proxy_type,),
                daemon=True
            )
            worker.start()
            threads.append(worker)
            time.sleep(0.01)
            
        # Monitor thread
        monitor = threading.Thread(target=self.monitor_views, daemon=True)
        monitor.start()
        threads.append(monitor)
        
        # Status display thread
        status = threading.Thread(target=self.show_status, daemon=True)
        status.start()
        threads.append(status)
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping...")
            self.running = False
            time.sleep(2)
            
    def _proxy_updater(self):
        """Periodic proxy updater"""
        while self.running:
            time.sleep(120)  # Update every 2 minutes
            self.proxy_manager.update_proxies()

# ==================== Main Execution ====================
if __name__ == "__main__":
    bot = TelegramViewBot()
    bot.run()
