#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram View Bot - Professional Edition
Version: 2.0
Author: Improved Version
"""

import sys
import os
import re
import logging
from time import sleep
from threading import Thread, active_count
from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Optional, Tuple, List
from enum import Enum
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from configparser import ConfigParser
from colorama import init, Fore, Style

# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Configuration
class Config:
    THREADS = 1000  # Increased thread count
    TIMEOUT = 10
    MAX_RETRIES = 3
    BATCH_SIZE = 100
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    
    # Proxy types
    PROXY_TYPES = ['http', 'socks4', 'socks5']
    
    # Regex patterns
    IP_PATTERN = r'(?:[1-9]|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])'
    PORT_PATTERN = r'(?:\d|[1-9]\d{1,3}|[1-5]\d{4}|6[0-4]\d{3}|65[0-4]\d{2}|655[0-2]\d|6553[0-5])'
    PROXY_REGEX = re.compile(
        fr"(?:^|\D)?(({IP_PATTERN}\.{IP_PATTERN}\.{IP_PATTERN}\.{IP_PATTERN}):({PORT_PATTERN}))(?:\D|$)"
    )

@dataclass
class ProxyStats:
    """Proxy statistics"""
    total: int = 0
    working: int = 0
    failed: int = 0
    token_errors: int = 0
    
class ProxyType(Enum):
    HTTP = 'http'
    SOCKS4 = 'socks4'
    SOCKS5 = 'socks5'

class TelegramViewBot:
    def __init__(self):
        self.setup_logging()
        self.load_config()
        self.setup_session()
        self.proxies = {pt: [] for pt in Config.PROXY_TYPES}
        self.stats = ProxyStats()
        self.channel = ""
        self.post = 0
        self.real_views = 0
        self.running = True
        
    def setup_logging(self):
        """Configure logging system"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('bot.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def load_config(self):
        """Load configuration from file"""
        self.config = ConfigParser(interpolation=None)
        if not self.config.read("config.ini", encoding="utf-8"):
            self.logger.error("config.ini not found!")
            sys.exit(1)
            
    def setup_session(self):
        """Setup requests session with retry strategy"""
        self.session = requests.Session()
        retry_strategy = Retry(
            total=Config.MAX_RETRIES,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=100, pool_maxsize=100)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
        
    def print_banner(self):
        """Display banner and stats"""
        self.clear_screen()
        banner = f"""
{Fore.CYAN}{'='*60}
{Fore.YELLOW}██╗  ██╗███████╗██╗     ██╗      ██████╗ 
{Fore.YELLOW}██║  ██║██╔════╝██║     ██║     ██╔═══██╗
{Fore.YELLOW}███████║█████╗  ██║     ██║     ██║   ██║
{Fore.YELLOW}██╔══██║██╔══╝  ██║     ██║     ██║   ██║
{Fore.YELLOW}██║  ██║███████╗███████╗███████╗╚██████╔╝
{Fore.YELLOW}╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝ ╚═════╝ 
{Fore.CYAN}{'='*60}
{Fore.GREEN}Channel: {self.channel} | Post: {self.post}
{Fore.GREEN}Real Views: {self.real_views}
{Fore.CYAN}{'='*60}
{Fore.MAGENTA}Proxies Total: {self.stats.total} | Working: {self.stats.working} | Failed: {self.stats.failed}
{Fore.MAGENTA}Token Errors: {self.stats.token_errors}
{Fore.CYAN}{'='*60}{Style.RESET_ALL}
"""
        print(banner)
        
    def scrape_proxies(self, sources: List[str], proxy_type: str) -> List[str]:
        """Scrape proxies from sources with improved error handling"""
        found_proxies = []
        
        for source in sources:
            if not source or not source.strip():
                continue
                
            try:
                response = self.session.get(
                    source.strip(), 
                    timeout=Config.TIMEOUT,
                    headers={'User-Agent': Config.USER_AGENT}
                )
                
                if response.status_code == 200:
                    matches = Config.PROXY_REGEX.findall(response.text)
                    for match in matches:
                        proxy = f"{match[0]}:{match[2]}"
                        found_proxies.append(proxy)
                        self.logger.debug(f"Found {proxy_type} proxy: {proxy}")
                        
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Error scraping {source}: {e}")
                continue
                
        return found_proxies
        
    def scrape_all_proxies(self):
        """Scrape proxies from all sources concurrently"""
        with ThreadPoolExecutor(max_workers=len(Config.PROXY_TYPES)) as executor:
            futures = []
            
            for proxy_type in Config.PROXY_TYPES:
                sources = self.config.get(proxy_type.upper(), "Sources", fallback="").splitlines()
                if sources:
                    future = executor.submit(self.scrape_proxies, sources, proxy_type)
                    futures.append((proxy_type, future))
                    
            # Clear existing proxies
            for pt in Config.PROXY_TYPES:
                self.proxies[pt].clear()
                
            # Collect results
            for proxy_type, future in futures:
                try:
                    proxies = future.result(timeout=30)
                    self.proxies[proxy_type].extend(proxies)
                    self.stats.total += len(proxies)
                    self.logger.info(f"Found {len(proxies)} {proxy_type} proxies")
                except Exception as e:
                    self.logger.error(f"Error scraping {proxy_type}: {e}")
                    
    def get_token(self, proxy: str, proxy_type: str) -> Optional[Tuple[str, requests.Session]]:
        """Get view token using proxy"""
        try:
            session = requests.Session()
            proxy_url = f"{proxy_type}://{proxy}"
            
            response = session.get(
                f'https://t.me/{self.channel}/{self.post}',
                params={'embed': '1', 'mode': 'tme'},
                headers={
                    'referer': f'https://t.me/{self.channel}/{self.post}',
                    'user-agent': Config.USER_AGENT
                },
                proxies={
                    'http': proxy_url,
                    'https': proxy_url
                },
                timeout=Config.TIMEOUT
            )
            
            if response.status_code == 200:
                token_match = re.search(r'data-view="([^"]+)', response.text)
                if token_match:
                    return token_match.group(1), session
                    
        except requests.exceptions.RequestException as e:
            self.logger.debug(f"Token error for {proxy}: {e}")
            
        return None
        
    def send_view(self, token: str, session: requests.Session, proxy: str, proxy_type: str) -> bool:
        """Send view using token"""
        try:
            proxy_url = f"{proxy_type}://{proxy}"
            cookies = session.cookies.get_dict()
            
            response = session.get(
                'https://t.me/v/',
                params={'views': token},
                cookies={
                    'stel_dt': '-240',
                    'stel_web_auth': 'https%3A%2F%2Fweb.telegram.org%2Fz%2F',
                    'stel_ssid': cookies.get('stel_ssid', ''),
                    'stel_on': cookies.get('stel_on', '')
                },
                headers={
                    'referer': f'https://t.me/{self.channel}/{self.post}?embed=1&mode=tme',
                    'user-agent': Config.USER_AGENT,
                    'x-requested-with': 'XMLHttpRequest'
                },
                proxies={
                    'http': proxy_url,
                    'https': proxy_url
                },
                timeout=Config.TIMEOUT
            )
            
            return response.status_code == 200 and response.text.strip() == 'true'
            
        except requests.exceptions.RequestException as e:
            self.logger.debug(f"View send error for {proxy}: {e}")
            return False
            
    def process_proxy(self, proxy: str, proxy_type: str):
        """Process a single proxy"""
        try:
            token_result = self.get_token(proxy, proxy_type)
            
            if token_result:
                token, session = token_result
                if self.send_view(token, session, proxy, proxy_type):
                    self.stats.working += 1
                else:
                    self.stats.failed += 1
            else:
                self.stats.token_errors += 1
                
        except Exception as e:
            self.logger.error(f"Error processing proxy {proxy}: {e}")
            self.stats.failed += 1
            
    def process_proxy_batch(self, proxy_queue: Queue):
        """Process a batch of proxies"""
        while self.running:
            try:
                proxy, proxy_type = proxy_queue.get(timeout=1)
                self.process_proxy(proxy, proxy_type)
                proxy_queue.task_done()
            except Empty:
                break
            except Exception as e:
                self.logger.error(f"Batch processing error: {e}")
                continue
                
    def start_view_worker(self):
        """Main worker function"""
        while self.running:
            # Scrape fresh proxies
            self.scrape_all_proxies()
            
            if not any(self.proxies.values()):
                self.logger.warning("No proxies found, retrying...")
                sleep(5)
                continue
                
            # Create proxy queue
            proxy_queue = Queue()
            for proxy_type, proxies in self.proxies.items():
                for proxy in proxies:
                    proxy_queue.put((proxy, proxy_type))
                    
            # Process proxies with thread pool
            with ThreadPoolExecutor(max_workers=Config.THREADS) as executor:
                futures = []
                for _ in range(min(Config.THREADS, proxy_queue.qsize())):
                    future = executor.submit(self.process_proxy_batch, proxy_queue)
                    futures.append(future)
                    
                # Wait for all tasks to complete
                proxy_queue.join()
                
    def check_views_worker(self):
        """Monitor real view count"""
        while self.running:
            try:
                response = self.session.get(
                    f'https://t.me/{self.channel}/{self.post}',
                    params={'embed': '1', 'mode': 'tme'},
                    headers={
                        'referer': f'https://t.me/{self.channel}/{self.post}',
                        'user-agent': Config.USER_AGENT
                    },
                    timeout=Config.TIMEOUT
                )
                
                if response.status_code == 200:
                    views_match = re.search(
                        r'<span class="tgme_widget_message_views">([^<]+)',
                        response.text
                    )
                    
                    if views_match:
                        views_text = views_match.group(1)
                        # Convert K/M suffixes to numbers
                        if 'K' in views_text:
                            self.real_views = int(float(views_text.replace('K', '')) * 1000)
                        elif 'M' in views_text:
                            self.real_views = int(float(views_text.replace('M', '')) * 1000000)
                        else:
                            self.real_views = int(views_text.replace(',', ''))
                            
                    self.print_banner()
                    
            except Exception as e:
                self.logger.error(f"View check error: {e}")
                
            sleep(2)
            
    def run(self):
        """Main execution method"""
        try:
            # Get target URL
            url = input(f"{Fore.CYAN}Telegram View Post URL ==> {Style.RESET_ALL}").strip()
            url_parts = url.replace('https://t.me/', '').split('/')
            
            if len(url_parts) != 2:
                self.logger.error("Invalid URL format!")
                return
                
            self.channel, self.post = url_parts[0], int(url_parts[1])
            
            # Start workers
            self.running = True
            view_thread = Thread(target=self.start_view_worker, daemon=True)
            check_thread = Thread(target=self.check_views_worker, daemon=True)
            
            view_thread.start()
            check_thread.start()
            
            # Keep main thread alive
            while view_thread.is_alive() and check_thread.is_alive():
                sleep(1)
                
        except KeyboardInterrupt:
            self.logger.info("Shutting down...")
            self.running = False
        except Exception as e:
            self.logger.error(f"Fatal error: {e}")
            
if __name__ == "__main__":
    # Check and install required packages
    required_packages = ['requests', 'colorama', 'urllib3']
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            os.system(f'pip install {package}')
            
    # Run bot
    bot = TelegramViewBot()
    bot.run()
