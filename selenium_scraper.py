"""
Selenium-based scraper with residential proxy support for VW and Volvo
This scraper uses a real Chrome browser to bypass Cloudflare protection
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time
import random

# Webshare proxy configuration
PROXY_HOST = "p.webshare.io"
PROXY_PORT = "80"
PROXY_USERNAME_BASE = "omyktwoo"
PROXY_PASSWORD = "hr8xkdwmscw2"

def create_proxy_extension(proxy_host, proxy_port, proxy_user, proxy_pass):
    """
    Create a Chrome extension for proxy authentication
    Chrome doesn't support proxy auth directly, so we need an extension
    """
    import zipfile
    import os
    
    manifest_json = """
    {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Chrome Proxy",
        "permissions": [
            "proxy",
            "tabs",
            "unlimitedStorage",
            "storage",
            "<all_urls>",
            "webRequest",
            "webRequestBlocking"
        ],
        "background": {
            "scripts": ["background.js"]
        },
        "minimum_chrome_version":"22.0.0"
    }
    """

    background_js = """
    var config = {
            mode: "fixed_servers",
            rules: {
              singleProxy: {
                scheme: "http",
                host: "%s",
                port: parseInt(%s)
              },
              bypassList: ["localhost"]
            }
          };

    chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

    function callbackFn(details) {
        return {
            authCredentials: {
                username: "%s",
                password: "%s"
            }
        };
    }

    chrome.webRequest.onAuthRequired.addListener(
                callbackFn,
                {urls: ["<all_urls>"]},
                ['blocking']
    );
    """ % (proxy_host, proxy_port, proxy_user, proxy_pass)

    # Create the extension directory
    plugin_path = "/tmp/proxy_auth_plugin.zip"
    
    with zipfile.ZipFile(plugin_path, 'w') as zp:
        zp.writestr("manifest.json", manifest_json)
        zp.writestr("background.js", background_js)
    
    return plugin_path

def setup_chrome_with_proxy(use_proxy=True, headless=False):
    """Setup Chrome with proxy and anti-detection measures"""
    chrome_options = Options()
    
    # Anti-detection settings
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Additional options
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--start-maximized')
    
    # Realistic user agent
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Headless mode (optional)
    if headless:
        chrome_options.add_argument('--headless=new')
    
    # Add proxy extension if using proxy
    if use_proxy:
        proxy_num = random.randint(1, 20)
        proxy_user = f"{PROXY_USERNAME_BASE}-{proxy_num}"
        plugin_path = create_proxy_extension(PROXY_HOST, PROXY_PORT, proxy_user, PROXY_PASSWORD)
        chrome_options.add_extension(plugin_path)
        print(f"Using proxy: {proxy_user}@{PROXY_HOST}:{PROXY_PORT}")
    
    # Initialize driver with webdriver-manager
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Set page load timeout
    driver.set_page_load_timeout(60)
    
    # Execute CDP commands to mask automation
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def wait_for_cloudflare(driver, max_wait=30):
    """Wait for Cloudflare challenge to complete"""
    print("  Waiting for Cloudflare challenge...")
    time.sleep(5)  # Initial wait
    
    start_time = time.time()
    while time.time() - start_time < max_wait:
        try:
            # Check if we're still on Cloudflare page
            page_source = driver.page_source.lower()
            if 'just a moment' in page_source or 'checking your browser' in page_source:
                print("  Still on Cloudflare challenge page, waiting...")
                time.sleep(3)
            else:
                print("  ✅ Cloudflare challenge passed!")
                return True
        except Exception as e:
            print(f"  Error checking page: {e}")
            time.sleep(2)
    
    print("  ⚠️ Cloudflare challenge timeout")
    return False

def scrape_page_selenium(driver, url):
    """Scrape a page using Selenium"""
    try:
        print(f"\n  Navigating to: {url}")
        driver.get(url)
        
        # Wait for Cloudflare
        if not wait_for_cloudflare(driver, max_wait=30):
            print("  ❌ Could not bypass Cloudflare")
            return None
        
        # Additional wait for page to fully load
        time.sleep(3)
        
        # Get page source
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        print(f"  Page title: {driver.title}")
        return soup
        
    except TimeoutException:
        print("  ❌ Page load timeout")
        return None
    except Exception as e:
        print(f"  ❌ Error: {str(e)[:100]}")
        return None

def extract_parts_from_soup(soup, base_url, make, brand):
    """Extract parts from BeautifulSoup object"""
    parts = []
    
    # Pattern 1: Elements with data-sku
    elements = soup.find_all(['div', 'button', 'article'], attrs={'data-sku': True})
    print(f"  Found {len(elements)} elements with SKU")
    
    for element in elements:
        sku = element.get('data-sku', 'N/A')
        name = element.get('data-name', element.get_text(strip=True)[:100])
        price_str = element.get('data-sale-price', element.get('data-price', '0'))
        
        try:
            price = float(price_str.replace('$', '').replace(',', '')) if price_str else 0.0
        except:
            price = 0.0
        
        if name and name != 'N/A':
            parts.append({
                'make': make,
                'brand': brand,
                'part_name': name,
                'part_number': sku,
                'price': price,
                'url': base_url
            })
    
    return parts

def scrape_make_selenium(make, base_url, brand, use_proxy=True):
    """Scrape a make using Selenium"""
    print(f"\n{'='*70}")
    print(f"SCRAPING {make} from {base_url}")
    print('='*70)
    
    driver = None
    all_parts = []
    
    try:
        # Setup Chrome with proxy
        driver = setup_chrome_with_proxy(use_proxy=use_proxy, headless=False)
        
        # Scrape homepage
        print("\nScraping homepage...")
        soup = scrape_page_selenium(driver, base_url)
        
        if soup:
            homepage_parts = extract_parts_from_soup(soup, base_url, make, brand)
            all_parts.extend(homepage_parts)
            print(f"  Found {len(homepage_parts)} parts on homepage")
            
            # Find category links
            links = soup.find_all('a', href=True)
            category_links = []
            
            for link in links:
                href = link['href']
                if '/a/' in href and base_url.split('//')[1].split('.')[0] in href:
                    if href not in category_links:
                        category_links.append(href)
            
            print(f"  Found {len(category_links)} category links")
            
            # Scrape up to 5 categories
            for i, cat_url in enumerate(category_links[:5], 1):
                print(f"\n  Scraping category {i}/5...")
                time.sleep(random.uniform(3, 5))
                
                cat_soup = scrape_page_selenium(driver, cat_url)
                if cat_soup:
                    cat_parts = extract_parts_from_soup(cat_soup, cat_url, make, brand)
                    all_parts.extend(cat_parts)
                    print(f"  Found {len(cat_parts)} parts in category")
        
        print(f"\n✅ Total {make} parts found: {len(all_parts)}")
        return all_parts
        
    except Exception as e:
        print(f"\n❌ Error scraping {make}: {e}")
        return []
    
    finally:
        if driver:
            driver.quit()
            print(f"  Browser closed")

def main():
    """Main scraping function"""
    print("="*70)
    print("SELENIUM SCRAPER WITH RESIDENTIAL PROXIES")
    print("="*70)
    print("This will open Chrome browsers to scrape VW and Volvo")
    print("The browsers will be visible so you can see the progress")
    print("="*70)
    
    all_parts = []
    
    # Sites to scrape
    sites = [
        ('VOLKSWAGEN', 'https://vw.oempartsonline.com', 'Volkswagen'),
        ('VOLVO', 'https://volvo.oempartsonline.com', 'Volvo'),
        ('TOYOTA', 'https://toyota.oempartsonline.com', 'Toyota'),  # Retry Toyota too
    ]
    
    for make, url, brand in sites:
        print(f"\n\nStarting {make} scraping...")
        parts = scrape_make_selenium(make, url, brand, use_proxy=True)
        all_parts.extend(parts)
        
        # Wait between makes
        if make != sites[-1][0]:
            print(f"\nWaiting 5 seconds before next make...")
            time.sleep(5)
    
    # Process results
    print("\n" + "="*70)
    print("SCRAPING COMPLETE")
    print("="*70)
    
    if all_parts:
        df = pd.DataFrame(all_parts)
        df = df.drop_duplicates(subset=['make', 'part_number'], keep='first')
        
        print(f"\nTotal unique parts scraped: {len(df)}")
        print("\nBreakdown by make:")
        for make in df['make'].unique():
            count = len(df[df['make'] == make])
            avg_price = df[df['make'] == make]['price'].mean()
            print(f"  {make}: {count} parts (avg: ${avg_price:.2f})")
        
        # Update database
        try:
            existing_df = pd.read_csv('oem_parts_data.csv')
            print(f"\nExisting database: {len(existing_df)} parts")
            
            # Remove old entries
            makes_scraped = df['make'].unique().tolist()
            existing_df = existing_df[~existing_df['make'].isin(makes_scraped)]
            print(f"After removing old entries: {len(existing_df)} parts")
            
            # Combine
            combined_df = pd.concat([existing_df, df], ignore_index=True)
            combined_df.to_csv('oem_parts_data.csv', index=False)
            
            print(f"\n✅ Updated oem_parts_data.csv")
            print(f"   Total parts: {len(combined_df):,}")
            print(f"   Total makes: {combined_df['make'].nunique()}")
            
            print("\nFinal counts for scraped makes:")
            for make in makes_scraped:
                count = len(combined_df[combined_df['make'] == make])
                print(f"  {make}: {count} parts")
        
        except FileNotFoundError:
            df.to_csv('oem_parts_data.csv', index=False)
            print(f"\n✅ Created oem_parts_data.csv with {len(df)} parts")
    
    else:
        print("\n⚠️ No parts were successfully scraped")

if __name__ == "__main__":
    print("\n" + "="*70)
    print("IMPORTANT: This scraper will open visible Chrome windows")
    print("You will see the browser navigating through pages")
    print("This is normal and helps bypass Cloudflare protection")
    print("="*70)
    input("\nPress ENTER to start scraping...")
    
    main()
