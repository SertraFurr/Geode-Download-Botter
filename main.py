import requests
import sys
import os
import re
import warnings
from urllib3.exceptions import InsecureRequestWarning
from concurrent.futures import ThreadPoolExecutor, as_completed

warnings.simplefilter('ignore', InsecureRequestWarning)

def load_proxies_from_file():
    if not os.path.exists('proxies.txt'):
        return []
    
    proxies = []
    try:
        with open('proxies.txt', 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if line.startswith('https://'):
                    proxy = line[8:]
                    print(f"Converted HTTPS proxy {line} to HTTP: {proxy}")
                elif line.startswith('http://'):
                    proxy = line[7:]
                elif re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+$', line):
                    proxy = line
                else:
                    continue 
                proxies.append(proxy)
        print(f"Loaded {len(proxies)} HTTP proxies from proxies.txt.")
        return proxies
    except Exception as e:
        print(f"Error reading proxies.txt: {e}")
        return []

def test_proxy(proxy, target_url):
    proxy_dict = {
        'http': f'http://{proxy}',
        'https': f'http://{proxy}'
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        resp = requests.get(target_url, proxies=proxy_dict, headers=headers, timeout=8, allow_redirects=False, verify=False)
        return resp.status_code == 302
    except:
        return False

def main():
    all_proxies = load_proxies_from_file()
    if not all_proxies:
        print("No HTTP proxies available in proxies.txt. Exiting.")
        sys.exit(1)
    
    mod_url = input("Enter the mod page URL (e.g., https://geode-sdk.org/mods/geode.node-ids): ").strip()
    if not mod_url:
        print("Invalid URL. Exiting.")
        sys.exit(1)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(mod_url, headers=headers, timeout=10, verify=False)
        response.raise_for_status()
        match = re.search(r'href="([^"]*api\.geode-sdk\.org/v1/mods/[^/]+/versions/[^/]+/download[^"]*)"', response.text)
        if match:
            target_url = match.group(1)
            print(f"Extracted download URL: {target_url}")
        else:
            print("Could not find download link in the page. Exiting.")
            sys.exit(1)
    except Exception as e:
        print(f"Error fetching mod page: {e}")
        sys.exit(1)
    
    try:
        num_desired = int(input("How many successful requests do you want? "))
        if num_desired <= 0:
            print("Invalid number. Exiting.")
            sys.exit(1)
    except ValueError:
        print("Invalid input. Exiting.")
        sys.exit(1)
    
    print("Starting...")
    working_proxies = []
    n = len(all_proxies)
    total = n
    completed = 0
    with ThreadPoolExecutor(max_workers=100) as executor:
        future_to_proxy = {executor.submit(test_proxy, proxy, target_url): proxy for proxy in all_proxies}
        for future in as_completed(future_to_proxy):
            proxy = future_to_proxy[future]
            try:
                if future.result():
                    working_proxies.append(proxy)
                    print(f"Download added. Total download added: {len(working_proxies)}")
                    
                    if len(working_proxies) >= num_desired:
                        pending_futures = [f for f in future_to_proxy if not f.done()]
                        for f in pending_futures:
                            f.cancel()
                        print(f"Did what the user asked, byeee!.")
                        
            except Exception as e:
                pass
            completed += 1
            if completed % 50 == 0:
                remaining = total - completed
                current_working = len(working_proxies)
                if current_working >= num_desired:
                    print("Stopping further progress updates.")
    
    print(f"\nCompleted. Total successful requests: {len(working_proxies)} / {n}")

if __name__ == "__main__":
    main()
