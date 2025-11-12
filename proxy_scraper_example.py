"""
Using Residential Proxies to Bypass Cloudflare Protection

OVERVIEW:
Residential proxies route your requests through real residential IP addresses,
making them appear as regular users rather than bots/scrapers.

PROXY PROVIDERS (Popular Options):
1. Bright Data (formerly Luminati) - https://brightdata.com
2. Smartproxy - https://smartproxy.com
3. Oxylabs - https://oxylabs.io
4. IPRoyal - https://iproyal.com
5. Webshare - https://webshare.io

SETUP STEPS:
1. Sign up for a proxy service (most offer free trials)
2. Get your proxy credentials (host, port, username, password)
3. Configure your scraper to use the proxy
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# ============================================================================
# METHOD 1: Using Basic Requests with Proxy
# ============================================================================

def scrape_with_basic_proxy():
    """
    Basic approach using requests library with proxy configuration
    """
    
    # PROXY CONFIGURATION
    # Replace with your actual proxy credentials
    PROXY_HOST = "proxy.provider.com"  # e.g., "brd.superproxy.io"
    PROXY_PORT = "12321"                # Your proxy port
    PROXY_USERNAME = "your_username"    # Your proxy username
    PROXY_PASSWORD = "your_password"    # Your proxy password
    
    # Format proxy URL
    proxy_url = f"http://{PROXY_USERNAME}:{PROXY_PASSWORD}@{PROXY_HOST}:{PROXY_PORT}"
    
    proxies = {
        'http': proxy_url,
        'https': proxy_url
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    url = 'https://toyota.oempartsonline.com'
    
    try:
        response = requests.get(
            url, 
            headers=headers, 
            proxies=proxies,
            timeout=30
        )
        
        if response.status_code == 200:
            print(f"✅ Successfully accessed {url}")
            soup = BeautifulSoup(response.content, 'html.parser')
            print(f"Page title: {soup.title.string if soup.title else 'No title'}")
            return response
        else:
            print(f"❌ Failed with status code: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


# ============================================================================
# METHOD 2: Using Cloudscraper with Proxy
# ============================================================================

def scrape_with_cloudscraper_proxy():
    """
    Using cloudscraper library with proxy for better Cloudflare bypass
    """
    try:
        import cloudscraper
    except ImportError:
        print("Installing cloudscraper...")
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "cloudscraper"])
        import cloudscraper
    
    # PROXY CONFIGURATION
    PROXY_HOST = "proxy.provider.com"
    PROXY_PORT = "12321"
    PROXY_USERNAME = "your_username"
    PROXY_PASSWORD = "your_password"
    
    proxy_url = f"http://{PROXY_USERNAME}:{PROXY_PASSWORD}@{PROXY_HOST}:{PROXY_PORT}"
    
    proxies = {
        'http': proxy_url,
        'https': proxy_url
    }
    
    # Create scraper with proxy
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'darwin',  # Use 'windows' or 'linux' if needed
            'desktop': True
        }
    )
    
    url = 'https://toyota.oempartsonline.com'
    
    try:
        response = scraper.get(url, proxies=proxies, timeout=30)
        
        if response.status_code == 200:
            print(f"✅ Successfully accessed {url}")
            soup = BeautifulSoup(response.content, 'html.parser')
            return response
        else:
            print(f"❌ Failed with status code: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


# ============================================================================
# METHOD 3: Using Selenium with Proxy (Most Reliable)
# ============================================================================

def scrape_with_selenium_proxy():
    """
    Using Selenium with proxy - most reliable for Cloudflare bypass
    Requires: pip install selenium
    Also needs ChromeDriver: brew install chromedriver (Mac)
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
    except ImportError:
        print("Installing selenium...")
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "selenium"])
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
    
    # PROXY CONFIGURATION
    PROXY_HOST = "proxy.provider.com"
    PROXY_PORT = "12321"
    PROXY_USERNAME = "your_username"
    PROXY_PASSWORD = "your_password"
    
    # Configure Chrome options
    chrome_options = Options()
    
    # Set proxy with authentication
    proxy_string = f"{PROXY_HOST}:{PROXY_PORT}"
    chrome_options.add_argument(f'--proxy-server=http://{proxy_string}')
    
    # Additional options to appear more human-like
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Uncomment to run headless (without visible browser)
    # chrome_options.add_argument('--headless')
    
    # For proxy authentication, you may need to use an extension
    # This is a workaround for Chrome proxy auth
    
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        # Set page load timeout
        driver.set_page_load_timeout(30)
        
        url = 'https://toyota.oempartsonline.com'
        driver.get(url)
        
        # Wait for page to load (Cloudflare check usually takes 5-10 seconds)
        time.sleep(10)
        
        # Wait for specific element to ensure page is loaded
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        print(f"✅ Successfully accessed {url}")
        print(f"Page title: {driver.title}")
        
        # Get page source
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Now you can scrape the page
        # ... your scraping logic here ...
        
        return soup
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None
        
    finally:
        if driver:
            driver.quit()


# ============================================================================
# METHOD 4: Using Rotating Proxies (Best for Large Scale)
# ============================================================================

def scrape_with_rotating_proxy_pool():
    """
    Using a pool of rotating residential proxies
    Best for scraping multiple pages/makes
    """
    
    # List of proxy servers (get from your provider)
    # Most providers offer a single gateway that auto-rotates
    PROXY_LIST = [
        {
            'host': 'proxy1.provider.com',
            'port': '12321',
            'username': 'user1',
            'password': 'pass1'
        },
        {
            'host': 'proxy2.provider.com',
            'port': '12322',
            'username': 'user2',
            'password': 'pass2'
        }
    ]
    
    # Or use rotating gateway (most common)
    ROTATING_GATEWAY = {
        'host': 'rotating.proxy.provider.com',  # e.g., 'brd.superproxy.io:22225'
        'port': '12321',
        'username': 'your_username-session-random',  # Note: -session-random for rotation
        'password': 'your_password'
    }
    
    def get_proxy_dict(proxy_config):
        proxy_url = f"http://{proxy_config['username']}:{proxy_config['password']}@{proxy_config['host']}:{proxy_config['port']}"
        return {'http': proxy_url, 'https': proxy_url}
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    }
    
    urls_to_scrape = [
        'https://toyota.oempartsonline.com',
        'https://vw.oempartsonline.com',
        'https://volvo.oempartsonline.com'
    ]
    
    results = []
    
    for url in urls_to_scrape:
        # Use rotating gateway
        proxies = get_proxy_dict(ROTATING_GATEWAY)
        
        try:
            response = requests.get(
                url,
                headers=headers,
                proxies=proxies,
                timeout=30
            )
            
            if response.status_code == 200:
                print(f"✅ Successfully scraped: {url}")
                soup = BeautifulSoup(response.content, 'html.parser')
                results.append({'url': url, 'soup': soup})
            else:
                print(f"⚠️ Failed {url}: Status {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error scraping {url}: {e}")
        
        # Be polite - wait between requests
        time.sleep(2)
    
    return results


# ============================================================================
# PRACTICAL EXAMPLE: Scrape VW with Proxy
# ============================================================================

def scrape_vw_with_proxy(proxy_config):
    """
    Practical example: Scrape VW parts using proxy
    
    Args:
        proxy_config (dict): Dictionary with host, port, username, password
    """
    
    proxy_url = f"http://{proxy_config['username']}:{proxy_config['password']}@{proxy_config['host']}:{proxy_config['port']}"
    
    proxies = {
        'http': proxy_url,
        'https': proxy_url
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    url = 'https://vw.oempartsonline.com'
    all_parts = []
    
    try:
        # Get homepage
        print(f"Accessing {url} via proxy...")
        response = requests.get(url, headers=headers, proxies=proxies, timeout=30)
        
        if response.status_code == 200:
            print("✅ Successfully bypassed Cloudflare!")
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Scrape featured products
            products = soup.find_all('div', attrs={'data-sku': True})
            print(f"Found {len(products)} products")
            
            for product in products:
                part = {
                    'make': 'VOLKSWAGEN',
                    'brand': 'Volkswagen',
                    'part_name': product.get('data-name', 'N/A'),
                    'part_number': product.get('data-sku', 'N/A'),
                    'price': float(product.get('data-sale-price', 0)),
                    'url': url
                }
                all_parts.append(part)
            
            # Get category links and scrape them
            links = soup.find_all('a', href=True)
            category_links = [link['href'] for link in links if '/a/' in link.get('href', '')]
            
            print(f"Found {len(category_links)} category links")
            
            for cat_url in category_links[:5]:  # Limit for example
                time.sleep(2)  # Be polite
                
                try:
                    cat_response = requests.get(cat_url, headers=headers, proxies=proxies, timeout=30)
                    if cat_response.status_code == 200:
                        cat_soup = BeautifulSoup(cat_response.content, 'html.parser')
                        cat_products = cat_soup.find_all('button', attrs={'data-sku': True})
                        
                        for product in cat_products:
                            part = {
                                'make': 'VOLKSWAGEN',
                                'brand': 'Volkswagen',
                                'part_name': product.get('data-name', 'N/A'),
                                'part_number': product.get('data-sku', 'N/A'),
                                'price': float(product.get('data-sale-price', 0)),
                                'url': cat_url
                            }
                            all_parts.append(part)
                            
                except Exception as e:
                    print(f"Error scraping category: {e}")
            
            # Save results
            if all_parts:
                df = pd.DataFrame(all_parts)
                df = df.drop_duplicates(subset=['part_number'])
                print(f"\n✅ Scraped {len(df)} unique VW parts")
                return df
            
        else:
            print(f"❌ Request failed with status: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    print("="*70)
    print("RESIDENTIAL PROXY SCRAPING GUIDE")
    print("="*70)
    print()
    print("To use this script, you need to:")
    print("1. Sign up for a proxy service (e.g., Bright Data, Smartproxy)")
    print("2. Get your proxy credentials")
    print("3. Replace the placeholder values in the functions above")
    print()
    print("Example proxy configuration:")
    print("-" * 70)
    
    example_config = {
        'host': 'brd.superproxy.io',
        'port': '22225',
        'username': 'brd-customer-hl_abc123-zone-residential',
        'password': 'your_password_here'
    }
    
    print(f"proxy_config = {example_config}")
    print()
    print("Then call:")
    print("df = scrape_vw_with_proxy(proxy_config)")
    print()
    print("=" * 70)
    print("PROXY PROVIDER RECOMMENDATIONS:")
    print("=" * 70)
    print()
    print("1. Bright Data (Best for enterprise)")
    print("   - Pros: Largest proxy pool, excellent success rate")
    print("   - Cons: More expensive ($500+/month)")
    print("   - Free trial: 7 days")
    print()
    print("2. Smartproxy (Good balance)")
    print("   - Pros: Good price/performance, easy to use")
    print("   - Cons: Smaller pool than Bright Data")
    print("   - Pricing: ~$75/month for 5GB")
    print()
    print("3. Webshare (Budget option)")
    print("   - Pros: Affordable, decent for small projects")
    print("   - Cons: Lower success rate with Cloudflare")
    print("   - Pricing: ~$45/month for 10GB")
    print()
    print("=" * 70)
    print("TIPS FOR SUCCESS:")
    print("=" * 70)
    print("✅ Use rotating residential proxies (not datacenter)")
    print("✅ Add delays between requests (1-3 seconds)")
    print("✅ Use realistic User-Agent headers")
    print("✅ Rotate proxies for each request")
    print("✅ Handle failures gracefully with retries")
    print("✅ Monitor your proxy usage/limits")
    print("=" * 70)
