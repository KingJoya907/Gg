#!/usr/bin/env python3
"""
Telegram Post View Bot - Professional Version
A multi-threaded tool to increase views on Telegram posts using proxy rotation.
"""

import os
import sys
import re
import logging
import threading
import time
from typing import List, Tuple, Optional, Union
from dataclasses import dataclass
from configparser import ConfigParser
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Try to import optional SOCKS support
try:
    import socks  # Requires PySocks
    SOCKS_AVAILABLE = True
except ImportError:
    SOCKS_AVAILABLE = False
    print("[WARNING] SOCKS proxy support not available. Install PySocks for SOCKS support.")


@dataclass
class ProxyConfig:
    """Proxy configuration data class"""
    http_sources: List[str]
    socks4_sources: List[str]
    socks5_sources: List[str]


@dataclass
class ViewResult:
    """Result of view attempt"""
    success: bool
    proxy: str
    proxy_type: str
    error_type: Optional[str] = None


class ProxyManager:
    """Manages proxy collection and validation"""
    
    IP_REGEX = re.compile(
        r"(?:^|\D)?("
        r"(?:[1-9]|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
        r"\."
        r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
        r"\."
        r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
        r"\."
        r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
        r":"
        r"(?:\d|[1-9]\d{1,3}|[1-5]\d{4}|6[0-4]\d{3}|65[0-4]\d{2}|655[0-2]\d|6553[0-5])"
        r")(?:\D|$)"
    )
    
    PROXY_TYPES = ('http', 'socks4', 'socks5')
    
    def __init__(self, config: ProxyConfig, timeout: int = 15):
        self.config = config
        self.timeout = timeout
        self.http_proxies: List[str] = []
        self.socks4_proxies: List[str] = []
        self.socks5_proxies: List[str] = []
        self.proxy_errors = 0
        
    def _fetch_proxies_from_source(self, source: str) -> List[str]:
        """Fetch proxies from a single source"""
        proxies = []
        try:
            response = requests.get(source, timeout=self.timeout)
            response.raise_for_status()
            
            matches = self.IP_REGEX.finditer(response.text)
            proxies = [match.group(1) for match in matches]
            
        except requests.RequestException as e:
            logging.error(f"Failed to fetch from {source}: {e}")
        except Exception as e:
            logging.error(f"Unexpected error fetching from {source}: {e}")
            
        return proxies
    
    def collect_proxies(self) -> Tuple[List[str], List[str], List[str]]:
        """Collect proxies from all sources"""
        logging.info("Starting proxy collection...")
        
        # Clear existing proxies
        self.http_proxies.clear()
        self.socks4_proxies.clear()
        self.socks5_proxies.clear()
        
        # Collect proxies from each source type
        with ThreadPoolExecutor(max_workers=10) as executor:
            # HTTP proxies
            http_futures = [
                executor.submit(self._fetch_proxies_from_source, source)
                for source in self.config.http_sources
            ]
            
            # SOCKS4 proxies
            socks4_futures = [
                executor.submit(self._fetch_proxies_from_source, source)
                for source in self.config.socks4_sources
            ]
            
            # SOCKS5 proxies
            socks5_futures = [
                executor.submit(self._fetch_proxies_from_source, source)
                for source in self.config.socks5_sources
            ]
            
            # Collect results
            for future in as_completed(http_futures + socks4_futures + socks5_futures):
                try:
                    proxies = future.result()
                    if future in http_futures:
                        self.http_proxies.extend(proxies)
                    elif future in socks4_futures:
                        self.socks4_proxies.extend(proxies)
                    elif future in socks5_futures:
                        self.socks5_proxies.extend(proxies)
                except Exception as e:
                    logging.error(f"Error collecting proxies: {e}")
        
        # Remove duplicates
        self.http_proxies = list(set(self.http_proxies))
        self.socks4_proxies = list(set(self.socks4_proxies))
        self.socks5_proxies = list(set(self.socks5_proxies))
        
        logging.info(f"Collected {len(self.http_proxies)} HTTP, "
                    f"{len(self.socks4_proxies)} SOCKS4, "
                    f"{len(self.socks5_proxies)} SOCKS5 proxies")
        
        return self.http_proxies, self.socks4_proxies, self.socks5_proxies


class TelegramViewBot:
    """Main bot class for Telegram view generation"""
    
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36'
    
    def __init__(self, channel: str, post_id: str, max_threads: int = 500, timeout: int = 15):
        self.channel = channel
        self.post_id = post_id
        self.max_threads = max_threads
        self.timeout = timeout
        self.view_counter = 0
        self.token_errors = 0
        self.view_success = 0
        self.running = True
        self.error_log = []
        
        # Setup logging
        self._setup_logging()
        
    def _setup_logging(self):
        """Configure logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('telegram_bot.log'),
                logging.StreamHandler()
            ]
        )
        
    def _create_session_with_retries(self) -> requests.Session:
        """Create a session with retry strategy"""
        session = requests.Session()
        retry_strategy = Retry(
            total=2,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
    
    def get_view_token(self, proxy: str, proxy_type: str) -> Union[Tuple[str, requests.Session], int]:
        """Get view token using proxy"""
        try:
            session = self._create_session_with_retries()
            
            response = session.get(
                f'https://t.me/{self.channel}/{self.post_id}',
                params={'embed': '1', 'mode': 'tme'},
                headers={
                    'referer': f'https://t.me/{self.channel}/{self.post_id}',
                    'user-agent': self.USER_AGENT
                },
                proxies={
                    'http': f'{proxy_type}://{proxy}',
                    'https': f'{proxy_type}://{proxy}'
                },
                timeout=self.timeout
            )
            
            token_match = re.search(r'data-view="([^"]+)', response.text)
            if token_match:
                return token_match.group(1), session
            return 2  # Token not found
            
        except AttributeError:
            return 2
        except requests.exceptions.RequestException:
            return 1  # Proxy error
        except Exception as e:
            logging.error(f"Error getting token: {e}")
            return 1
            
    def send_view(self, token: str, session: requests.Session, proxy: str, proxy_type: str) -> bool:
        """Send view request with token"""
        try:
            cookies_dict = session.cookies.get_dict()
            
            response = session.get(
                'https://t.me/v/',
                params={'views': token},
                cookies={
                    'stel_dt': '-240',
                    'stel_web_auth': 'https%3A%2F%2Fweb.telegram.org%2Fz%2F',
                    'stel_ssid': cookies_dict.get('stel_ssid', None),
                    'stel_on': cookies_dict.get('stel_on', None)
                },
                headers={
                    'referer': f'https://t.me/{self.channel}/{self.post_id}?embed=1&mode=tme',
                    'user-agent': self.USER_AGENT,
                    'x-requested-with': 'XMLHttpRequest'
                },
                proxies={
                    'http': f'{proxy_type}://{proxy}',
                    'https': f'{proxy_type}://{proxy}'
                },
                timeout=self.timeout
            )
            
            return response.status_code == 200 and response.text.strip() == 'true'
            
        except requests.exceptions.RequestException:
            return False
        except Exception as e:
            logging.error(f"Error sending view: {e}")
            return False
            
    def process_proxy(self, proxy: str, proxy_type: str) -> ViewResult:
        """Process a single proxy for view generation"""
        token_result = self.get_view_token(proxy, proxy_type)
        
        if token_result == 2:
            self.token_errors += 1
            return ViewResult(False, proxy, proxy_type, "token_not_found")
        elif token_result == 1:
            self.proxy_manager.proxy_errors += 1
            return ViewResult(False, proxy, proxy_type, "proxy_error")
        elif isinstance(token_result, tuple):
            success = self.send_view(token_result[0], token_result[1], proxy, proxy_type)
            if success:
                self.view_success += 1
                return ViewResult(True, proxy, proxy_type)
            else:
                return ViewResult(False, proxy, proxy_type, "send_failed")
        
        return ViewResult(False, proxy, proxy_type, "unknown_error")
    
    def monitor_views(self):
        """Monitor and display current view count"""
        while self.running:
            try:
                session = self._create_session_with_retries()
                response = session.get(
                    f'https://t.me/{self.channel}/{self.post_id}',
                    params={'embed': '1', 'mode': 'tme'},
                    headers={
                        'referer': f'https://t.me/{self.channel}/{self.post_id}',
                        'user-agent': self.USER_AGENT
                    },
                    timeout=self.timeout
                )
                
                views_match = re.search(
                    r'<span class="tgme_widget_message_views">([^<]+)',
                    response.text
                )
                
                if views_match:
                    current_views = views_match.group(1)
                    logging.info(f"Current views: {current_views}")
                    
                time.sleep(5)
                
            except Exception as e:
                logging.error(f"Error monitoring views: {e}")
                time.sleep(10)
    
    def run(self, proxy_manager: ProxyManager):
        """Main execution loop"""
        self.proxy_manager = proxy_manager
        
        logging.info(f"Starting view bot for channel: {self.channel}, post: {self.post_id}")
        logging.info(f"Max threads: {self.max_threads}")
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=self.monitor_views, daemon=True)
        monitor_thread.start()
        
        try:
            while self.running:
                # Collect fresh proxies
                http_proxies, socks4_proxies, socks5_proxies = proxy_manager.collect_proxies()
                
                # Prepare proxy list with types
                all_proxies = []
                all_proxies.extend([(p, 'http') for p in http_proxies])
                all_proxies.extend([(p, 'socks4') for p in socks4_proxies])
                all_proxies.extend([(p, 'socks5') for p in socks5_proxies])
                
                if not all_proxies:
                    logging.warning("No proxies found, waiting before retry...")
                    time.sleep(30)
                    continue
                
                logging.info(f"Processing {len(all_proxies)} proxies...")
                
                # Process proxies with thread pool
                with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
                    futures = [
                        executor.submit(self.process_proxy, proxy, proxy_type)
                        for proxy, proxy_type in all_proxies
                    ]
                    
                    success_count = 0
                    for future in as_completed(futures):
                        try:
                            result = future.result()
                            if result.success:
                                success_count += 1
                                
                            # Log progress periodically
                            if success_count % 100 == 0 and success_count > 0:
                                logging.info(f"Successfully sent {success_count} views")
                                
                        except Exception as e:
                            logging.error(f"Error processing future: {e}")
                
                logging.info(f"Cycle complete. Success: {success_count}, "
                           f"Token errors: {self.token_errors}, "
                           f"Proxy errors: {proxy_manager.proxy_errors}")
                
                # Small delay before next cycle
                time.sleep(5)
                
        except KeyboardInterrupt:
            logging.info("Received interrupt signal, shutting down...")
            self.running = False
        except Exception as e:
            logging.error(f"Unexpected error in main loop: {e}")
            self.running = False


def load_config(config_file: str = 'config.ini') -> Optional[ProxyConfig]:
    """Load configuration from file"""
    config_parser = ConfigParser(interpolation=None)
    
    try:
        if not config_parser.read(config_file, encoding="utf-8"):
            logging.error(f"Config file '{config_file}' not found!")
            return None
            
        http_sources = config_parser.get("HTTP", "Sources", fallback="").splitlines()
        socks4_sources = config_parser.get("SOCKS4", "Sources", fallback="").splitlines()
        socks5_sources = config_parser.get("SOCKS5", "Sources", fallback="").splitlines()
        
        # Remove empty strings
        http_sources = [s for s in http_sources if s.strip()]
        socks4_sources = [s for s in socks4_sources if s.strip()]
        socks5_sources = [s for s in socks5_sources if s.strip()]
        
        return ProxyConfig(http_sources, socks4_sources, socks5_sources)
        
    except Exception as e:
        logging.error(f"Error loading config: {e}")
        return None


def parse_post_url(url: str) -> Tuple[str, str]:
    """Parse Telegram post URL to extract channel and post ID"""
    # Remove protocol and domain
    parsed = url.replace('https://t.me/', '').replace('http://t.me/', '')
    
    # Split into parts
    parts = parsed.split('/')
    
    if len(parts) >= 2:
        return parts[0], parts[1]
    else:
        raise ValueError("Invalid Telegram post URL format")


def main():
    """Main entry point"""
    # Clear screen
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print("=" * 60)
    print("Telegram Post View Bot - Professional Edition")
    print("=" * 60)
    print()
    
    # Check SOCKS support
    if not SOCKS_AVAILABLE:
        print("[WARNING] SOCKS proxy support is limited. Install PySocks for full SOCKS support.")
        print("          pip install PySocks")
        print()
    
    # Get post URL
    while True:
        try:
            url_input = input("Enter Telegram Post URL: ").strip()
            if not url_input:
                continue
                
            channel, post_id = parse_post_url(url_input)
            break
        except ValueError as e:
            print(f"Error: {e}")
            print("Please enter a valid URL like: https://t.me/channel/123")
    
    print()
    
    # Get thread count
    try:
        threads_input = input("Number of threads (default 500): ").strip()
        max_threads = int(threads_input) if threads_input else 500
    except ValueError:
        max_threads = 500
        print(f"Using default: {max_threads}")
    
    # Load configuration
    config = load_config()
    if not config:
        print("\n[ERROR] Failed to load config.ini")
        print("Please create a config.ini file with HTTP, SOCKS4, and SOCKS5 sections")
        print("Example:")
        print("[HTTP]")
        print("Sources = https://example.com/proxies.txt")
        print()
        sys.exit(1)
    
    print(f"\nConfiguration loaded:")
    print(f"  HTTP sources: {len(config.http_sources)}")
    print(f"  SOCKS4 sources: {len(config.socks4_sources)}")
    print(f"  SOCKS5 sources: {len(config.socks5_sources)}")
    print()
    
    # Initialize components
    proxy_manager = ProxyManager(config, timeout=15)
    bot = TelegramViewBot(channel, post_id, max_threads=max_threads)
    
    print(f"Starting bot for: {channel}/{post_id}")
    print("Press Ctrl+C to stop")
    print()
    
    # Run bot
    try:
        bot.run(proxy_manager)
    except KeyboardInterrupt:
        print("\n\nBot stopped by user")
    except Exception as e:
        print(f"\n[ERROR] Bot crashed: {e}")
        logging.error(f"Fatal error: {e}", exc_info=True)
    
    print("\nFinal Statistics:")
    print(f"  Views sent: {bot.view_success}")
    print(f"  Token errors: {bot.token_errors}")
    print(f"  Proxy errors: {proxy_manager.proxy_errors}")
    print("\nLog saved to telegram_bot.log")


if __name__ == "__main__":
    main()
