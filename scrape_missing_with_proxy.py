"""
Enhanced scraper with better proxy handling for Cloudflare-protected sites
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random

# Webshare proxy configuration
PROXY_HOST = "p.webshare.io"
PROXY_PORT = "80"
PROXY_USERNAME_BASE = "omyktwoo"
PROXY_PASSWORD = "hr8xkdwmscw2"
NUM_PROXIES = 20

def get_random_proxy():
    """Get a random proxy from the pool"""
    proxy_num = random.randint(1, NUM_PROXIES)
    username = f"{PROXY_USERNAME_BASE}-{proxy_num}"
    proxy_url = f"http://{username}:{PROXY_PASSWORD}@{PROXY_HOST}:{PROXY_PORT}"
    return {
        'http': proxy_url,
        'https': proxy_url
    }

def get_headers():
    """Return realistic browser headers"""
    return {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
        'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"'
    }

def scrape_with_proxy(url, max_retries=5):
    """Scrape with proxy and retries"""
    for attempt in range(max_retries):
        try:
            proxies = get_random_proxy()
            print(f"  Attempt {attempt + 1}/{max_retries}...")
            
            response = requests.get(
                url,
                headers=get_headers(),
                proxies=proxies,
                timeout=30,
                allow_redirects=True
            )
            
            if response.status_code == 200:
                # Check if it's a Cloudflare challenge page
                if 'Just a moment' in response.text or 'checking your browser' in response.text.lower():
                    print(f"  ⚠️ Cloudflare challenge detected, rotating proxy...")
                    time.sleep(3)
                    continue
                
                print(f"  ✅ Success!")
                return response
            else:
                print(f"  ⚠️ Status {response.status_code}")
                time.sleep(2)
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)[:80]}")
            time.sleep(2)
    
    return None

def scrape_oempartsonline_site(make, subdomain, brand):
    """Scrape from oempartsonline.com sites"""
    print(f"\n{'='*70}")
    print(f"SCRAPING {make} from {subdomain}.oempartsonline.com")
    print('='*70)
    
    base_url = f"https://{subdomain}.oempartsonline.com"
    all_parts = []
    
    # Scrape homepage
    print(f"Scraping homepage: {base_url}")
    response = scrape_with_proxy(base_url)
    
    if not response:
        print(f"❌ Could not access {make} homepage")
        return []
    
    soup = BeautifulSoup(response.content, 'html.parser')
    print(f"Page title: {soup.title.string if soup.title else 'No title'}")
    
    # Extract featured products
    featured = soup.find_all('div', attrs={'data-sku': True, 'data-name': True})
    print(f"Found {len(featured)} featured products")
    
    for product in featured:
        sku = product.get('data-sku', 'N/A')
        name = product.get('data-name', 'N/A')
        price_str = product.get('data-sale-price', product.get('data-price', '0'))
        
        try:
            price = float(price_str) if price_str else 0.0
        except:
            price = 0.0
        
        parent_link = product.find_parent('a')
        url = parent_link['href'] if parent_link and parent_link.get('href') else base_url
        if not url.startswith('http'):
            url = base_url + url
        
        all_parts.append({
            'make': make,
            'brand': brand,
            'part_name': name,
            'part_number': sku,
            'price': price,
            'url': url
        })
    
    # Find category links
    links = soup.find_all('a', href=True)
    category_links = set()
    
    for link in links:
        href = link['href']
        if f'{subdomain}.oempartsonline.com/a/' in href:
            category_links.add(href)
    
    category_links = list(category_links)
    print(f"Found {len(category_links)} category links")
    
    # Scrape categories (limit to 10)
    for i, cat_url in enumerate(category_links[:10], 1):
        print(f"\nScraping category {i}/{min(len(category_links), 10)}: {cat_url.split('/')[-1][:40]}...")
        time.sleep(random.uniform(2, 4))  # Random delay
        
        cat_response = scrape_with_proxy(cat_url)
        if not cat_response:
            continue
        
        cat_soup = BeautifulSoup(cat_response.content, 'html.parser')
        
        # Extract products from category
        products = cat_soup.find_all('button', attrs={'data-sku': True})
        print(f"  Found {len(products)} products")
        
        for product in products:
            sku = product.get('data-sku', 'N/A')
            name = product.get('data-name', 'N/A')
            price_str = product.get('data-sale-price', product.get('data-price', '0'))
            
            try:
                price = float(price_str) if price_str else 0.0
            except:
                price = 0.0
            
            all_parts.append({
                'make': make,
                'brand': brand,
                'part_name': name,
                'part_number': sku,
                'price': price,
                'url': cat_url
            })
        
        # Check for pagination
        next_button = cat_soup.find('a', {'aria-label': 'Next'})
        if next_button and next_button.get('href'):
            next_url = next_button['href']
            if not next_url.startswith('http'):
                next_url = base_url + next_url
            
            print(f"  Found next page, scraping...")
            time.sleep(random.uniform(2, 4))
            
            next_response = scrape_with_proxy(next_url)
            if next_response:
                next_soup = BeautifulSoup(next_response.content, 'html.parser')
                next_products = next_soup.find_all('button', attrs={'data-sku': True})
                print(f"  Found {len(next_products)} more products on page 2")
                
                for product in next_products:
                    sku = product.get('data-sku', 'N/A')
                    name = product.get('data-name', 'N/A')
                    price_str = product.get('data-sale-price', product.get('data-price', '0'))
                    
                    try:
                        price = float(price_str) if price_str else 0.0
                    except:
                        price = 0.0
                    
                    all_parts.append({
                        'make': make,
                        'brand': brand,
                        'part_name': name,
                        'part_number': sku,
                        'price': price,
                        'url': next_url
                    })
    
    print(f"\n✅ Total {make} parts found: {len(all_parts)}")
    return all_parts

def main():
    """Main function to scrape VW, Toyota, and Volvo"""
    print("="*70)
    print("ENHANCED SCRAPING WITH WEBSHARE RESIDENTIAL PROXIES")
    print("="*70)
    print(f"Proxy: {PROXY_HOST}:{PROXY_PORT}")
    print(f"Pool: {NUM_PROXIES} rotating proxies")
    print("="*70)
    
    all_parts = []
    
    # Try scraping from oempartsonline.com with proxies
    makes_to_scrape = [
        ('VOLKSWAGEN', 'vw', 'Volkswagen'),
        ('TOYOTA', 'toyota', 'Toyota'),
        ('VOLVO', 'volvo', 'Volvo')
    ]
    
    for make, subdomain, brand in makes_to_scrape:
        parts = scrape_oempartsonline_site(make, subdomain, brand)
        all_parts.extend(parts)
        time.sleep(3)  # Delay between makes
    
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
            print(f"  {make}: {count} parts (avg price: ${avg_price:.2f})")
        
        # Update database
        try:
            existing_df = pd.read_csv('oem_parts_data.csv')
            print(f"\nExisting database: {len(existing_df)} parts")
            
            # Remove old entries for these makes
            existing_df = existing_df[~existing_df['make'].isin(['VOLKSWAGEN', 'TOYOTA', 'VOLVO'])]
            print(f"After removing old entries: {len(existing_df)} parts")
            
            # Combine
            combined_df = pd.concat([existing_df, df], ignore_index=True)
            combined_df.to_csv('oem_parts_data.csv', index=False)
            
            print(f"\n✅ Updated oem_parts_data.csv")
            print(f"   Total parts: {len(combined_df)}")
            print(f"   Total makes: {combined_df['make'].nunique()}")
            
            # Show updated counts
            print("\nUpdated make counts:")
            for make in ['VOLKSWAGEN', 'TOYOTA', 'VOLVO']:
                count = len(combined_df[combined_df['make'] == make])
                print(f"  {make}: {count} parts")
        
        except FileNotFoundError:
            df.to_csv('oem_parts_data.csv', index=False)
            print(f"\n✅ Created oem_parts_data.csv with {len(df)} parts")
    
    else:
        print("\n⚠️ No parts were successfully scraped")

if __name__ == "__main__":
    main()
