#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║     ██╗ ██████╗ ██╗   ██╗ █████╗     ██╗   ██╗██╗███████╗██╗    ██╗         ║
║     ██║██╔═══██╗╚██╗ ██╔╝██╔══██╗    ██║   ██║██║██╔════╝██║    ██║         ║
║     ██║██║   ██║ ╚████╔╝ ███████║    ██║   ██║██║█████╗  ██║ █╗ ██║         ║
║     ██║██║   ██║  ╚██╔╝  ██╔══██║    ╚██╗ ██╔╝██║██╔══╝  ██║███╗██║         ║
║     ██║╚██████╔╝   ██║   ██║  ██║     ╚████╔╝ ██║███████╗╚███╔███╔╝         ║
║     ╚═╝ ╚═════╝    ╚═╝   ╚═╝  ╚═╝      ╚═══╝  ╚═╝╚══════╝ ╚══╝╚══╝          ║
║                                                                               ║
║     ████████╗███████╗██╗     ███████╗ ██████╗ ██████╗  █████╗ ███╗   ███╗   ║
║     ╚══██╔══╝██╔════╝██║     ██╔════╝██╔════╝ ██╔══██╗██╔══██╗████╗ ████║   ║
║        ██║   █████╗  ██║     █████╗  ██║  ███╗██████╔╝███████║██╔████╔██║   ║
║        ██║   ██╔══╝  ██║     ██╔══╝  ██║   ██║██╔══██╗██╔══██║██║╚██╔╝██║   ║
║        ██║   ███████╗███████╗███████╗╚██████╔╝██║  ██║██║  ██║██║ ╚═╝ ██║   ║
║        ╚═╝   ╚══════╝╚══════╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝   ║
║                                                                               ║
║                          ╔═══════════════════════╗                           ║
║                          ║    JOYA VIEW v2.0     ║                           ║
║                          ║  Telegram View Bot    ║                           ║
║                          ╚═══════════════════════╝                           ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import re
import time
import threading
from datetime import datetime
from configparser import ConfigParser

# Colors for terminal
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
CYAN = '\033[96m'
MAGENTA = '\033[95m'
WHITE = '\033[97m'
RESET = '\033[0m'
BOLD = '\033[1m'

# Box drawing characters
TOP_LEFT = '╔'
TOP_RIGHT = '╗'
BOTTOM_LEFT = '╚'
BOTTOM_RIGHT = '╝'
HORIZONTAL = '═'
VERTICAL = '║'
CROSS = '╟'
LINE = '─'

# Install required packages
try:
    import requests
except ImportError:
    print(f"{YELLOW}[!] Installing requests...{RESET}")
    os.system('pip install requests > /dev/null 2>&1')
    import requests

# Configuration
THREADS = 500
PROXIES_TYPES = ('http', 'socks4', 'socks5')
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
TIMEOUT = 15

# Proxy regex pattern
REGEX = re.compile(r"(?:^|\D)?(("+ r"(?:[1-9]|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"\." + r"(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])"
                + r"):" + (r"(?:\d|[1-9]\d{1,3}|[1-5]\d{4}|6[0-4]\d{3}"
                + r"|65[0-4]\d{2}|655[0-2]\d|6553[0-5])")
                + r")(?:\D|$)")

def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    """Print the Joya View banner"""
    clear_screen()
    banner = f"""
{CYAN}╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║     {GREEN}██╗ ██████╗ ██╗   ██╗ █████╗     ██╗   ██╗██╗███████╗██╗    ██╗{CYAN}         ║
║     {GREEN}██║██╔═══██╗╚██╗ ██╔╝██╔══██╗    ██║   ██║██║██╔════╝██║    ██║{CYAN}         ║
║     {GREEN}██║██║   ██║ ╚████╔╝ ███████║    ██║   ██║██║█████╗  ██║ █╗ ██║{CYAN}         ║
║     {GREEN}██║██║   ██║  ╚██╔╝  ██╔══██║    ╚██╗ ██╔╝██║██╔══╝  ██║███╗██║{CYAN}         ║
║     {GREEN}██║╚██████╔╝   ██║   ██║  ██║     ╚████╔╝ ██║███████╗╚███╔███╔╝{CYAN}         ║
║     {GREEN}╚═╝ ╚═════╝    ╚═╝   ╚═╝  ╚═╝      ╚═══╝  ╚═╝╚══════╝ ╚══╝╚══╝{CYAN}          ║
║                                                                               ║
║     {BLUE}████████╗███████╗██╗     ███████╗ ██████╗ ██████╗  █████╗ ███╗   ███╗{CYAN}   ║
║     {BLUE}╚══██╔══╝██╔════╝██║     ██╔════╝██╔════╝ ██╔══██╗██╔══██╗████╗ ████║{CYAN}   ║
║        {BLUE}██║   █████╗  ██║     █████╗  ██║  ███╗██████╔╝███████║██╔████╔██║{CYAN}   ║
║        {BLUE}██║   ██╔══╝  ██║     ██╔══╝  ██║   ██║██╔══██╗██╔══██║██║╚██╔╝██║{CYAN}   ║
║        {BLUE}██║   ███████╗███████╗███████╗╚██████╔╝██║  ██║██║  ██║██║ ╚═╝ ██║{CYAN}   ║
║        {BLUE}╚═╝   ╚══════╝╚══════╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝{CYAN}   ║
║                                                                               ║
║                          {YELLOW}╔═══════════════════════╗{CYAN}                           ║
║                          {YELLOW}║    JOYA VIEW v2.0     ║{CYAN}                           ║
║                          {YELLOW}║  Telegram View Bot    ║{CYAN}                           ║
║                          {YELLOW}╚═══════════════════════╝{CYAN}                           ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝{RESET}
"""
    print(banner)

# Load config file
errors = open('errors.txt', 'a+')
cfg = ConfigParser(interpolation=None)
cfg.read("config.ini", encoding="utf-8")

http, socks4, socks5 = '', '', ''
try:
    http = cfg["HTTP"]
    socks4 = cfg["SOCKS4"]
    socks5 = cfg["SOCKS5"]
except KeyError:
    print_banner()
    print(f"\n{RED}╔═══════════════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{RED}║                      CONFIGURATION ERROR                              ║{RESET}")
    print(f"{RED}║                    config.ini file not found!                         ║{RESET}")
    print(f"{RED}╚═══════════════════════════════════════════════════════════════════════╝{RESET}")
    time.sleep(3)
    exit()

http_proxies, socks4_proxies, socks5_proxies = [], [], []
proxy_errors, token_errors = 0, 0
channel, post, real_views = '', 0, 0

def print_stats():
    """Print statistics in a nice box"""
    print(f"\n{CYAN}╔═══════════════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{CYAN}║{RESET}                      {BOLD}LIVE STATISTICS{RESET}                           {CYAN}║{RESET}")
    print(f"{CYAN}╠═══════════════════════════════════════════════════════════════════════╣{RESET}")
    print(f"{CYAN}║{RESET}  Channel: {GREEN}{channel:<20}{RESET}  Post: {GREEN}{post:<10}{RESET}              {CYAN}║{RESET}")
    print(f"{CYAN}╠═══════════════════════════════════════════════════════════════════════╣{RESET}")
    print(f"{CYAN}║{RESET}  {BOLD}Current Views:{RESET} {GREEN}{real_views:<10}{RESET}  {BOLD}Views Sent:{RESET} {GREEN}0{RESET}                  {CYAN}║{RESET}")
    print(f"{CYAN}║{RESET}  {BOLD}Bad Tokens:{RESET} {RED}{token_errors:<8}{RESET}  {BOLD}Proxy Errors:{RESET} {RED}{proxy_errors:<8}{RESET}           {CYAN}║{RESET}")
    print(f"{CYAN}╠═══════════════════════════════════════════════════════════════════════╣{RESET}")
    print(f"{CYAN}║{RESET}  {BOLD}HTTP Proxies:{RESET} {BLUE}{len(http_proxies):<8}{RESET}  {BOLD}SOCKS4:{RESET} {BLUE}{len(socks4_proxies):<8}{RESET}            {CYAN}║{RESET}")
    print(f"{CYAN}║{RESET}  {BOLD}SOCKS5:{RESET} {BLUE}{len(socks5_proxies):<8}{RESET}  {BOLD}Total:{RESET} {BLUE}{len(http_proxies)+len(socks4_proxies)+len(socks5_proxies):<8}{RESET}      {CYAN}║{RESET}")
    print(f"{CYAN}╚═══════════════════════════════════════════════════════════════════════╝{RESET}")

def scrap(sources, _proxy_type):
    for source in sources:
        if source:
            try:
                response = requests.get(source, timeout=TIMEOUT)
                if tuple(REGEX.finditer(response.text)):
                    for proxy in tuple(REGEX.finditer(response.text)):
                        if _proxy_type == 'http':
                            http_proxies.append(proxy.group(1))
                        elif _proxy_type == 'socks4':
                            socks4_proxies.append(proxy.group(1))
                        elif _proxy_type == 'socks5':
                            socks5_proxies.append(proxy.group(1))
            except Exception as e:
                errors.write(f'{e}\n')

def start_scrap():
    threads = []
    for i in (http_proxies, socks4_proxies, socks5_proxies):
        i.clear()

    for i in ((http.get("Sources").splitlines(), 'http'),
              (socks4.get("Sources").splitlines(), 'socks4'),
              (socks5.get("Sources").splitlines(), 'socks5')):

        thread = Thread(target=scrap, args=(i[0], i[1]))
        threads.append(thread)
        thread.start()

    for t in threads:
        t.join()

def get_token(proxy, proxy_type):
    try:
        session = requests.session()
        response = session.get(
            f'https://t.me/{channel}/{post}',
            params={'embed': '1', 'mode': 'tme'},
            headers={
                'referer': f'https://t.me/{channel}/{post}',
                'user-agent': USER_AGENT
            },
            proxies={
                'http': f'{proxy_type}://{proxy}',
                'https': f'{proxy_type}://{proxy}'
            },
            timeout=TIMEOUT)

        return search('data-view="([^"]+)', response.text).group(1), session

    except AttributeError:
        return 2
    except requests.exceptions.RequestException:
        return 1
    except Exception as e:
        errors.write(f'{e}\n')
        return None

def send_view(token, session, proxy, proxy_type):
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
                'referer': f'https://t.me/{channel}/{post}?embed=1&mode=tme',
                'user-agent': USER_AGENT,
                'x-requested-with': 'XMLHttpRequest'
            },
            proxies={
                'http': f'{proxy_type}://{proxy}',
                'https': f'{proxy_type}://{proxy}'
            },
            timeout=TIMEOUT)

        return True if (response.status_code == 200 and response.text == 'true') else False

    except requests.exceptions.RequestException:
        return 1
    except Exception:
        pass

def control(proxy, proxy_type):
    global proxy_errors, token_errors

    token_data = get_token(proxy, proxy_type)

    if token_data == 2:
        token_errors += 1
    elif token_data == 1:
        proxy_errors += 1
    elif token_data:
        send_data = send_view(token_data[0], token_data[1], proxy, proxy_type)
        if send_data == 1:
            proxy_errors += 1

def start_view():
    c, threads = 0, []
    start_scrap()

    for i in [http_proxies, socks4_proxies, socks5_proxies]:
        for j in i:
            thread = Thread(target=control, args=(j, PROXIES_TYPES[c]))
            threads.append(thread)

            while active_count() > THREADS:
                sleep(0.05)

            thread.start()

        c += 1
        sleep(2)

    for t in threads:
        t.join()

def check_views():
    global real_views

    while True:
        try:
            telegram_request = requests.get(
                f'https://t.me/{channel}/{post}',
                params={'embed': '1', 'mode': 'tme'},
                headers={
                    'referer': f'https://t.me/{channel}/{post}',
                    'user-agent': USER_AGENT
                })

            views = search('<span class="tgme_widget_message_views">([^<]+)', telegram_request.text)
            if views:
                real_views = views.group(1)
            
            # Update display
            print_stats()
            sleep(2)

        except:
            pass

def main():
    """Main function"""
    global channel, post
    
    print_banner()
    
    # Get post URL
    print(f"\n{CYAN}╔═══════════════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{CYAN}║{RESET}                      {BOLD}INPUT REQUIRED{RESET}                              {CYAN}║{RESET}")
    print(f"{CYAN}╚═══════════════════════════════════════════════════════════════════════╝{RESET}\n")
    
    url = input(f"{GREEN}[?]{RESET} Enter Telegram Post URL: ").strip()
    
    try:
        channel, post = url.replace('https://t.me/', '').split('/')
        print(f"\n{YELLOW}[!]{RESET} Starting bot for {GREEN}{channel}/{post}{RESET}")
        print(f"{YELLOW}[!]{RESET} Press {RED}Ctrl+C{RESET} to stop\n")
        time.sleep(2)
        
        # Start threads
        Thread(target=start_view, daemon=True).start()
        Thread(target=check_views, daemon=True).start()
        
        # Keep main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print(f"\n\n{RED}╔═══════════════════════════════════════════════════════════════════════╗{RESET}")
        print(f"{RED}║                      BOT STOPPED BY USER                               ║{RESET}")
        print(f"{RED}╚═══════════════════════════════════════════════════════════════════════╝{RESET}")
        print(f"\n{GREEN}[✓]{RESET} Total Views Sent: 0")
        print(f"{YELLOW}[!]{RESET} Bad Tokens: {token_errors}")
        print(f"{RED}[✗]{RESET} Proxy Errors: {proxy_errors}\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n{RED}[✗]{RESET} Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
