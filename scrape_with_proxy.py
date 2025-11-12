"""
Scrape VW, Toyota, and Volvo parts using Webshare residential proxies
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

# Number of proxies available (rotating pool)
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
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0'
    }

def scrape_page_with_retry(url, max_retries=3):
    """Scrape a page with retries using rotating proxies"""
    for attempt in range(max_retries):
        try:
            proxies = get_random_proxy()
            print(f"  Attempt {attempt + 1}/{max_retries} using proxy...")
            
            response = requests.get(
                url,
                headers=get_headers(),
                proxies=proxies,
                timeout=30,
                verify=True
            )
            
            if response.status_code == 200:
                print(f"  ✅ Success! Status: {response.status_code}")
                return response
            else:
                print(f"  ⚠️ Status {response.status_code}, retrying...")
                time.sleep(2)
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)[:100]}")
            if attempt < max_retries - 1:
                time.sleep(3)
            
    print(f"  ❌ Failed after {max_retries} attempts")
    return None

def extract_parts_generic(soup, base_url, make, brand):
    """Extract parts from page using multiple patterns"""
    parts = []
    
    # Pattern 1: Elements with data-sku attribute
    elements_with_sku = soup.find_all(['div', 'button', 'article', 'a'], attrs={'data-sku': True})
    print(f"    Found {len(elements_with_sku)} elements with SKU")
    
    for element in elements_with_sku:
        sku = element.get('data-sku', 'N/A')
        name = element.get('data-name', element.get('data-product-name', ''))
        
        # Try multiple price attributes
        price_str = element.get('data-sale-price') or element.get('data-price') or element.get('data-product-price', '0')
        
        try:
            # Remove currency symbols and convert to float
            price_str = price_str.replace('$', '').replace(',', '').strip()
            price = float(price_str) if price_str else 0.0
        except:
            price = 0.0
        
        # Get URL if available
        url = element.get('href', '')
        if url and not url.startswith('http'):
            url = base_url + url
        elif not url:
            url = base_url
        
        if name and name != 'N/A':
            parts.append({
                'make': make,
                'brand': brand,
                'part_name': name,
                'part_number': sku,
                'price': price,
                'url': url
            })
    
    # Pattern 2: Look for product cards with price elements
    product_cards = soup.find_all(['div', 'article'], class_=lambda x: x and ('product' in str(x).lower() or 'part' in str(x).lower()))
    print(f"    Found {len(product_cards)} product cards")
    
    for card in product_cards[:50]:  # Limit to avoid processing too many
        # Try to extract name
        name_elem = card.find(['h2', 'h3', 'h4', 'a', 'span'], class_=lambda x: x and ('title' in str(x).lower() or 'name' in str(x).lower()))
        if not name_elem:
            name_elem = card.find('a', href=True)
        
        name = name_elem.get_text(strip=True) if name_elem else ''
        
        # Try to extract price
        price_elem = card.find(['span', 'div'], class_=lambda x: x and 'price' in str(x).lower())
        price_text = price_elem.get_text(strip=True) if price_elem else '0'
        
        try:
            price_text = price_text.replace('$', '').replace(',', '').strip()
            price = float(price_text) if price_text else 0.0
        except:
            price = 0.0
        
        # Try to extract SKU
        sku_elem = card.find(['span', 'div'], class_=lambda x: x and ('sku' in str(x).lower() or 'part' in str(x).lower()))
        sku = sku_elem.get_text(strip=True) if sku_elem else name[:20]
        
        # Get URL
        link = card.find('a', href=True)
        url = link['href'] if link else base_url
        if url and not url.startswith('http'):
            url = base_url + url
        
        if name and len(name) > 3:
            parts.append({
                'make': make,
                'brand': brand,
                'part_name': name[:200],
                'part_number': sku[:100],
                'price': price,
                'url': url
            })
    
    return parts

def scrape_vw_parts():
    """Scrape VW parts from parts.vw.com"""
    print("\n" + "="*70)
    print("SCRAPING VOLKSWAGEN (parts.vw.com)")
    print("="*70)
    
    url = "https://parts.vw.com/"
    response = scrape_page_with_retry(url)
    
    if not response:
        return []
    
    soup = BeautifulSoup(response.content, 'html.parser')
    title = soup.title.string if soup.title else "No title"
    print(f"  Page title: {title}")
    
    parts = extract_parts_generic(soup, url, 'VOLKSWAGEN', 'Volkswagen')
    
    # Look for catalog/category links
    links = soup.find_all('a', href=True)
    category_links = []
    
    for link in links:
        href = link['href']
        if any(keyword in href.lower() for keyword in ['/parts/', '/catalog', '/shop', '/category', '/browse']):
            if href.startswith('http') or href.startswith('/'):
                full_url = href if href.startswith('http') else url.rstrip('/') + href
                if full_url not in category_links and full_url != url:
                    category_links.append(full_url)
    
    print(f"  Found {len(category_links)} category links")
    
    # Scrape up to 5 category pages
    for i, cat_url in enumerate(category_links[:5], 1):
        print(f"\n  Scraping category {i}/5: {cat_url[:60]}...")
        time.sleep(2)  # Be polite
        
        cat_response = scrape_page_with_retry(cat_url)
        if cat_response:
            cat_soup = BeautifulSoup(cat_response.content, 'html.parser')
            cat_parts = extract_parts_generic(cat_soup, url, 'VOLKSWAGEN', 'Volkswagen')
            parts.extend(cat_parts)
            print(f"    Found {len(cat_parts)} parts in this category")
    
    print(f"\n  Total VW parts found: {len(parts)}")
    return parts

def scrape_toyota_parts():
    """Scrape Toyota parts from www.toyotapartsdeal.com"""
    print("\n" + "="*70)
    print("SCRAPING TOYOTA (www.toyotapartsdeal.com)")
    print("="*70)
    
    url = "https://www.toyotapartsdeal.com/"
    response = scrape_page_with_retry(url)
    
    if not response:
        return []
    
    soup = BeautifulSoup(response.content, 'html.parser')
    title = soup.title.string if soup.title else "No title"
    print(f"  Page title: {title}")
    
    parts = extract_parts_generic(soup, url, 'TOYOTA', 'Toyota')
    
    # Look for catalog/category links
    links = soup.find_all('a', href=True)
    category_links = []
    
    for link in links:
        href = link['href']
        text = link.get_text(strip=True).lower()
        
        # Look for parts-related links
        if any(keyword in href.lower() or keyword in text for keyword in ['parts', 'catalog', 'shop', 'accessories', 'oem']):
            if href.startswith('http') or href.startswith('/'):
                full_url = href if href.startswith('http') else url.rstrip('/') + href
                if full_url not in category_links and full_url != url:
                    category_links.append(full_url)
    
    print(f"  Found {len(category_links)} potential category links")
    
    # Scrape up to 5 category pages
    for i, cat_url in enumerate(category_links[:5], 1):
        print(f"\n  Scraping category {i}/5: {cat_url[:60]}...")
        time.sleep(2)
        
        cat_response = scrape_page_with_retry(cat_url)
        if cat_response:
            cat_soup = BeautifulSoup(cat_response.content, 'html.parser')
            cat_parts = extract_parts_generic(cat_soup, url, 'TOYOTA', 'Toyota')
            parts.extend(cat_parts)
            print(f"    Found {len(cat_parts)} parts in this category")
    
    print(f"\n  Total Toyota parts found: {len(parts)}")
    return parts

def scrape_volvo_parts():
    """Scrape Volvo parts from usparts.volvocars.com"""
    print("\n" + "="*70)
    print("SCRAPING VOLVO (usparts.volvocars.com)")
    print("="*70)
    
    url = "https://usparts.volvocars.com/"
    response = scrape_page_with_retry(url)
    
    if not response:
        return []
    
    soup = BeautifulSoup(response.content, 'html.parser')
    title = soup.title.string if soup.title else "No title"
    print(f"  Page title: {title}")
    
    parts = extract_parts_generic(soup, url, 'VOLVO', 'Volvo')
    
    # Look for catalog/category links
    links = soup.find_all('a', href=True)
    category_links = []
    
    for link in links:
        href = link['href']
        text = link.get_text(strip=True).lower()
        
        if any(keyword in href.lower() or keyword in text for keyword in ['parts', 'catalog', 'shop', 'accessories', 'oem']):
            if href.startswith('http') or href.startswith('/'):
                full_url = href if href.startswith('http') else url.rstrip('/') + href
                if full_url not in category_links and full_url != url:
                    category_links.append(full_url)
    
    print(f"  Found {len(category_links)} potential category links")
    
    # Scrape up to 5 category pages
    for i, cat_url in enumerate(category_links[:5], 1):
        print(f"\n  Scraping category {i}/5: {cat_url[:60]}...")
        time.sleep(2)
        
        cat_response = scrape_page_with_retry(cat_url)
        if cat_response:
            cat_soup = BeautifulSoup(cat_response.content, 'html.parser')
            cat_parts = extract_parts_generic(cat_soup, url, 'VOLVO', 'Volvo')
            parts.extend(cat_parts)
            print(f"    Found {len(cat_parts)} parts in this category")
    
    print(f"\n  Total Volvo parts found: {len(parts)}")
    return parts

def main():
    """Main scraping function"""
    print("="*70)
    print("SCRAPING WITH WEBSHARE RESIDENTIAL PROXIES")
    print("="*70)
    print(f"Proxy host: {PROXY_HOST}:{PROXY_PORT}")
    print(f"Proxy pool: {NUM_PROXIES} rotating proxies")
    print("="*70)
    
    all_parts = []
    
    # Scrape VW
    vw_parts = scrape_vw_parts()
    all_parts.extend(vw_parts)
    time.sleep(3)
    
    # Scrape Toyota
    toyota_parts = scrape_toyota_parts()
    all_parts.extend(toyota_parts)
    time.sleep(3)
    
    # Scrape Volvo
    volvo_parts = scrape_volvo_parts()
    all_parts.extend(volvo_parts)
    
    # Process results
    print("\n" + "="*70)
    print("SCRAPING COMPLETE")
    print("="*70)
    
    if all_parts:
        df = pd.DataFrame(all_parts)
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['make', 'part_number'], keep='first')
        
        # Remove entries with no name or price
        df = df[df['part_name'].str.len() > 3]
        
        print(f"\nTotal parts scraped: {len(df)}")
        print("\nBreakdown by make:")
        for make in df['make'].unique():
            count = len(df[df['make'] == make])
            print(f"  {make}: {count} parts")
        
        # Load existing database
        try:
            existing_df = pd.read_csv('oem_parts_data.csv')
            print(f"\nExisting database: {len(existing_df)} parts")
            
            # Remove old entries for these makes
            existing_df = existing_df[~existing_df['make'].isin(['VOLKSWAGEN', 'TOYOTA', 'VOLVO'])]
            print(f"After removing old VW/Toyota/Volvo: {len(existing_df)} parts")
            
            # Combine
            combined_df = pd.concat([existing_df, df], ignore_index=True)
            combined_df.to_csv('oem_parts_data.csv', index=False)
            
            print(f"\n✅ Updated oem_parts_data.csv")
            print(f"   Total parts in database: {len(combined_df)}")
            print(f"   Total makes: {combined_df['make'].nunique()}")
            
        except FileNotFoundError:
            df.to_csv('oem_parts_data.csv', index=False)
            print(f"\n✅ Created new oem_parts_data.csv with {len(df)} parts")
    
    else:
        print("\n⚠️ No parts were scraped successfully")
        print("This could be due to:")
        print("  - Strong bot protection on the websites")
        print("  - Sites requiring JavaScript to load content")
        print("  - Different HTML structure than expected")
        print("\nYou may need to use Selenium for browser automation")

if __name__ == "__main__":
    main()
