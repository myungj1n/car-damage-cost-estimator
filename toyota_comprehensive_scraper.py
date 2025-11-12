"""
Comprehensive Toyota parts scraper for toyotapartsdeal.com
Using residential proxies to get extensive Toyota parts data
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from urllib.parse import urljoin

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
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

def scrape_with_retry(url, max_retries=3):
    """Scrape URL with retries"""
    for attempt in range(max_retries):
        try:
            proxies = get_random_proxy()
            response = requests.get(
                url,
                headers=get_headers(),
                proxies=proxies,
                timeout=30,
                allow_redirects=True
            )
            
            if response.status_code == 200:
                return response
            else:
                print(f"  Attempt {attempt+1}: Status {response.status_code}")
                time.sleep(2)
                
        except Exception as e:
            print(f"  Attempt {attempt+1}: Error - {str(e)[:80]}")
            time.sleep(2)
    
    return None

def extract_toyota_parts(soup, page_url):
    """Extract Toyota parts from page"""
    parts = []
    
    # Look for product listings
    # Pattern 1: Product cards with specific classes
    product_divs = soup.find_all(['div', 'article', 'li'], class_=lambda x: x and any(
        keyword in str(x).lower() for keyword in ['product', 'part', 'item-box', 'catalog-item']
    ))
    
    print(f"    Found {len(product_divs)} potential product containers")
    
    for product in product_divs[:100]:  # Limit to avoid too much processing
        # Extract part name
        name_elem = product.find(['h2', 'h3', 'h4', 'a', 'span'], class_=lambda x: x and any(
            keyword in str(x).lower() for keyword in ['title', 'name', 'product-name', 'part-name']
        ))
        
        if not name_elem:
            name_elem = product.find('a', href=lambda x: x and '/oem-' in str(x))
        
        name = name_elem.get_text(strip=True) if name_elem else ''
        
        # Extract price
        price_elem = product.find(['span', 'div', 'strong'], class_=lambda x: x and 'price' in str(x).lower())
        if not price_elem:
            price_elem = product.find(['span', 'div'], string=lambda x: x and '$' in str(x))
        
        price_text = price_elem.get_text(strip=True) if price_elem else '0'
        
        # Clean price
        try:
            price_text = price_text.replace('$', '').replace(',', '').strip()
            # Extract first number if multiple prices
            import re
            price_match = re.search(r'[\d.]+', price_text)
            price = float(price_match.group()) if price_match else 0.0
        except:
            price = 0.0
        
        # Extract part number/SKU
        sku_elem = product.find(['span', 'div'], class_=lambda x: x and any(
            keyword in str(x).lower() for keyword in ['sku', 'part-number', 'partnumber', 'part_number']
        ))
        
        if not sku_elem:
            # Try to find it in the text
            sku_text = product.get_text()
            import re
            sku_match = re.search(r'(?:Part|SKU|#)[\s:]*([A-Z0-9\-]+)', sku_text, re.IGNORECASE)
            sku = sku_match.group(1) if sku_match else name[:30]
        else:
            sku = sku_elem.get_text(strip=True)
        
        # Get product URL
        link = product.find('a', href=True)
        url = urljoin(page_url, link['href']) if link else page_url
        
        if name and len(name) > 3 and price >= 0:
            parts.append({
                'make': 'TOYOTA',
                'brand': 'Toyota',
                'part_name': name[:200],
                'part_number': sku[:100],
                'price': price,
                'url': url
            })
    
    return parts

def scrape_category_page(url, depth=0, max_depth=2):
    """Scrape a category page and follow pagination"""
    print(f"\n{'  ' * depth}Scraping: {url.split('/')[-1][:50]}...")
    
    response = scrape_with_retry(url)
    if not response:
        return []
    
    soup = BeautifulSoup(response.content, 'html.parser')
    all_parts = extract_toyota_parts(soup, url)
    
    print(f"{'  ' * depth}  Found {len(all_parts)} parts on this page")
    
    # Look for pagination (next page)
    next_links = soup.find_all('a', class_=lambda x: x and 'next' in str(x).lower())
    if not next_links:
        next_links = soup.find_all('a', string=lambda x: x and ('next' in str(x).lower() or '›' in str(x) or '»' in str(x)))
    
    for next_link in next_links[:1]:  # Only follow first next link
        next_url = urljoin(url, next_link['href'])
        if next_url != url and 'page=' in next_url:
            print(f"{'  ' * depth}  Following pagination...")
            time.sleep(random.uniform(2, 4))
            next_parts = scrape_category_page(next_url, depth=depth, max_depth=max_depth)
            all_parts.extend(next_parts)
            break  # Only follow one pagination link
    
    return all_parts

def find_category_links(soup, base_url):
    """Find all category/catalog links"""
    category_links = set()
    
    # Look for navigation menus
    nav_sections = soup.find_all(['nav', 'div', 'ul'], class_=lambda x: x and any(
        keyword in str(x).lower() for keyword in ['menu', 'nav', 'categories', 'catalog']
    ))
    
    for nav in nav_sections:
        links = nav.find_all('a', href=True)
        for link in links:
            href = link['href']
            # Filter for category/part pages
            if any(keyword in href.lower() for keyword in ['/category/', '/parts/', '/oem-', '/catalog/']):
                full_url = urljoin(base_url, href)
                if full_url.startswith(base_url):
                    category_links.add(full_url)
    
    # Also look for direct links to parts
    all_links = soup.find_all('a', href=True)
    for link in all_links:
        href = link['href']
        text = link.get_text(strip=True).lower()
        
        if any(keyword in href.lower() for keyword in ['/oem-toyota-', '/category/toyota-', '/parts/toyota-']):
            full_url = urljoin(base_url, href)
            if full_url.startswith(base_url) and full_url != base_url:
                category_links.add(full_url)
    
    return list(category_links)

def main():
    """Main scraping function for Toyota parts"""
    print("="*70)
    print("COMPREHENSIVE TOYOTA PARTS SCRAPER")
    print("Site: toyotapartsdeal.com")
    print("="*70)
    
    base_url = "https://www.toyotapartsdeal.com/"
    all_parts = []
    
    # Step 1: Scrape homepage
    print("\nStep 1: Scraping homepage...")
    response = scrape_with_retry(base_url)
    
    if not response:
        print("❌ Could not access homepage")
        return
    
    soup = BeautifulSoup(response.content, 'html.parser')
    print(f"Page title: {soup.title.string if soup.title else 'No title'}")
    
    # Extract parts from homepage
    homepage_parts = extract_toyota_parts(soup, base_url)
    all_parts.extend(homepage_parts)
    print(f"Found {len(homepage_parts)} parts on homepage")
    
    # Step 2: Find all category links
    print("\nStep 2: Finding category links...")
    category_links = find_category_links(soup, base_url)
    print(f"Found {len(category_links)} category links")
    
    # Display some sample links
    for i, link in enumerate(category_links[:10], 1):
        print(f"  {i}. {link.split('/')[-1][:60]}")
    
    # Step 3: Scrape each category
    print(f"\nStep 3: Scraping categories (limiting to 20 for speed)...")
    
    for i, category_url in enumerate(category_links[:20], 1):
        print(f"\nCategory {i}/{min(len(category_links), 20)}")
        time.sleep(random.uniform(2, 4))  # Be polite
        
        category_parts = scrape_category_page(category_url)
        all_parts.extend(category_parts)
        
        print(f"  Total parts so far: {len(all_parts)}")
    
    # Process results
    print("\n" + "="*70)
    print("SCRAPING COMPLETE")
    print("="*70)
    
    if all_parts:
        df = pd.DataFrame(all_parts)
        
        # Remove duplicates
        print(f"\nTotal parts scraped: {len(df)}")
        df = df.drop_duplicates(subset=['part_number'], keep='first')
        print(f"Unique parts: {len(df)}")
        
        # Filter out invalid entries
        df = df[df['part_name'].str.len() > 3]
        df = df[df['price'] > 0]  # Only keep parts with valid prices
        print(f"Valid parts with prices: {len(df)}")
        
        # Show price statistics
        print(f"\nPrice range: ${df['price'].min():.2f} - ${df['price'].max():.2f}")
        print(f"Average price: ${df['price'].mean():.2f}")
        
        # Show sample parts
        print("\nSample parts:")
        for idx, row in df.head(10).iterrows():
            print(f"  {row['part_name'][:50]:.<50} ${row['price']:.2f}")
        
        # Update database
        try:
            existing_df = pd.read_csv('oem_parts_data.csv')
            print(f"\nExisting database: {len(existing_df)} parts")
            
            # Remove old Toyota entries
            existing_df = existing_df[existing_df['make'] != 'TOYOTA']
            print(f"After removing old Toyota: {len(existing_df)} parts")
            
            # Combine
            combined_df = pd.concat([existing_df, df], ignore_index=True)
            combined_df.to_csv('oem_parts_data.csv', index=False)
            
            print(f"\n✅ Updated oem_parts_data.csv")
            print(f"   Total parts in database: {len(combined_df):,}")
            print(f"   Toyota parts: {len(df):,}")
            print(f"   Total makes: {combined_df['make'].nunique()}")
            
        except FileNotFoundError:
            df.to_csv('oem_parts_data.csv', index=False)
            print(f"\n✅ Created oem_parts_data.csv with {len(df)} Toyota parts")
    
    else:
        print("\n⚠️ No parts were successfully scraped")

if __name__ == "__main__":
    main()
