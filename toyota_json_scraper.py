"""
Toyota Parts Scraper - JSON Extraction Method
Extracts parts data from embedded JSON in page scripts
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import json
from urllib.parse import urljoin

# Webshare proxy configuration
PROXY_BASE = 'http://omyktwoo-{}:hr8xkdwmscw2@p.webshare.io:80'
PROXIES = [PROXY_BASE.format(i) for i in range(1, 21)]
current_proxy_idx = 0

def get_rotating_proxy():
    """Get next proxy from the rotation pool"""
    global current_proxy_idx
    proxy_url = PROXIES[current_proxy_idx]
    current_proxy_idx = (current_proxy_idx + 1) % len(PROXIES)
    return {'http': proxy_url, 'https': proxy_url}

def extract_json_from_page(soup):
    """Extract product data from embedded JSON in page scripts"""
    scripts = soup.find_all('script')
    for script in scripts:
        if script.string and 'partNumber' in script.string:
            script_text = script.string
            
            # Look for array of product objects with partNumber field
            # The data is in format: [[{partNumber:...}],[{partNumber:...}],...]
            try:
                # Find start of product arrays
                start_idx = 0
                products = []
                
                # Look for pattern: ],[{partNumber:
                # This indicates nested arrays of products
                while True:
                    start = script_text.find('[{"partNumber":', start_idx)
                    if start == -1:
                        break
                    
                    # Find the closing bracket for this product
                    bracket_count = 0
                    i = start
                    while i < len(script_text):
                        if script_text[i] == '[':
                            bracket_count += 1
                        elif script_text[i] == ']':
                            bracket_count -= 1
                            if bracket_count == 0:
                                # Found complete product array
                                json_text = script_text[start:i+1]
                                product_data = json.loads(json_text)
                                # Flatten if nested array
                                if isinstance(product_data, list) and len(product_data) > 0:
                                    if isinstance(product_data[0], dict):
                                        products.extend(product_data)
                                    else:
                                        # Nested list, flatten
                                        for item in product_data:
                                            if isinstance(item, list):
                                                products.extend(item)
                                break
                        i += 1
                    
                    start_idx = i + 1
                    
                if products:
                    return products
                    
            except Exception as e:
                pass
    
    return []

def extract_toyota_parts_from_json(json_data, page_url):
    """Extract part information from JSON data"""
    parts = []
    
    for item in json_data:
        try:
            part_number = item.get('partNumber', '').strip()
            description = item.get('mainPartDescription', '').strip()
            other_name = item.get('otherName', '').strip()
            
            # Get price from nested priceInfo object
            price_info = item.get('priceInfo', {})
            price = price_info.get('price', '0')
            retail_price = price_info.get('retail', '0')
            
            # Get URL
            part_url = item.get('url', '')
            if part_url and not part_url.startswith('http'):
                part_url = urljoin('https://www.toyotapartsdeal.com', part_url)
            
            # Create full part name
            if other_name:
                part_name = f"{description} - {other_name}"
            else:
                part_name = description
            
            # Convert price to float
            try:
                price_float = float(price) if price else 0.0
            except (ValueError, TypeError):
                price_float = 0.0
            
            if part_number and part_name and price_float > 0:
                parts.append({
                    'make': 'Toyota',
                    'part_number': part_number,
                    'part_name': part_name,
                    'price': price_float,
                    'url': part_url
                })
        except Exception as e:
            print(f"  Error processing item: {e}")
            continue
    
    return parts

def scrape_category_page(url, retries=3):
    """Scrape a single category page and extract parts from JSON"""
    for attempt in range(retries):
        try:
            proxies = get_rotating_proxy()
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            }
            
            print(f"  Fetching {url} (attempt {attempt + 1}/{retries})...")
            response = requests.get(url, headers=headers, proxies=proxies, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract JSON data
                json_data = extract_json_from_page(soup)
                if json_data:
                    parts = extract_toyota_parts_from_json(json_data, url)
                    print(f"  ✓ Found {len(parts)} parts")
                    return parts
                else:
                    print(f"  ⚠ No JSON data found")
                    return []
            else:
                print(f"  ✗ HTTP {response.status_code}")
                
        except Exception as e:
            print(f"  ✗ Error: {e}")
            if attempt < retries - 1:
                time.sleep(2)
    
    return []

def find_main_categories(homepage_url='https://www.toyotapartsdeal.com/'):
    """Find main category pages from homepage"""
    try:
        proxies = get_rotating_proxy()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        }
        
        print(f"Finding main categories from {homepage_url}...")
        response = requests.get(homepage_url, headers=headers, proxies=proxies, timeout=30)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find category links (start with /category/)
        category_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith('/category/') and href.endswith('.html'):
                full_url = urljoin(homepage_url, href)
                if full_url not in category_links:
                    category_links.append(full_url)
        
        print(f"Found {len(category_links)} main categories")
        return category_links
        
    except Exception as e:
        print(f"Error finding categories: {e}")
        return []

def find_part_listings_from_category(category_url):
    """Find all part listing pages from a category page"""
    try:
        proxies = get_rotating_proxy()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        }
        
        response = requests.get(category_url, headers=headers, proxies=proxies, timeout=30)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find part listing links (start with /oem-)
        part_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith('/oem-') and href.endswith('.html'):
                full_url = urljoin('https://www.toyotapartsdeal.com/', href)
                if full_url not in part_links:
                    part_links.append(full_url)
        
        return part_links
        
    except Exception as e:
        print(f"  Error getting part listings: {e}")
        return []

def scrape_all_toyota_parts():
    """Main function to scrape all Toyota parts"""
    print("=" * 80)
    print("TOYOTA PARTS SCRAPER - JSON EXTRACTION METHOD")
    print("=" * 80)
    
    all_parts = []
    
    # Step 1: Find main categories
    category_pages = find_main_categories()
    
    if not category_pages:
        print("\nNo categories found. Exiting.")
        return
    
    # Step 2: For each category, find part listing pages
    print(f"\nFinding part listings from {len(category_pages)} categories...")
    all_part_listings = set()
    
    for idx, category_url in enumerate(category_pages, 1):
        print(f"[{idx}/{len(category_pages)}] {category_url}")
        part_listings = find_part_listings_from_category(category_url)
        print(f"  Found {len(part_listings)} part listings")
        all_part_listings.update(part_listings)
        time.sleep(0.5)
    
    all_part_listings = list(all_part_listings)
    print(f"\nTotal unique part listing pages: {len(all_part_listings)}")
    
    # Step 3: Scrape each part listing page
    print(f"\nScraping {len(all_part_listings)} part listing pages...")
    for idx, part_url in enumerate(all_part_listings, 1):
        print(f"\n[{idx}/{len(all_part_listings)}] {part_url}")
        
        parts = scrape_category_page(part_url)
        all_parts.extend(parts)
        
        # Be polite - rate limiting
        time.sleep(1)
    
    # Remove duplicates based on part_number
    print("\n" + "=" * 80)
    print("DEDUPLICATION")
    print("=" * 80)
    print(f"Total parts scraped: {len(all_parts)}")
    
    df = pd.DataFrame(all_parts)
    if not df.empty:
        df = df.drop_duplicates(subset=['part_number'], keep='first')
        print(f"Unique parts after deduplication: {len(df)}")
        
        # Filter out parts with zero price
        df = df[df['price'] > 0]
        print(f"Valid parts (price > 0): {len(df)}")
        
        # Update the main database
        print("\n" + "=" * 80)
        print("DATABASE UPDATE")
        print("=" * 80)
        
        csv_file = 'oem_parts_data.csv'
        
        try:
            # Load existing data
            existing_df = pd.read_csv(csv_file)
            print(f"Existing database: {len(existing_df)} parts")
            
            # Remove old Toyota entries
            existing_df = existing_df[existing_df['make'] != 'Toyota']
            print(f"After removing old Toyota entries: {len(existing_df)} parts")
            
            # Add new Toyota parts
            combined_df = pd.concat([existing_df, df], ignore_index=True)
            print(f"After adding new Toyota parts: {len(combined_df)} parts")
            
            # Save
            combined_df.to_csv(csv_file, index=False)
            print(f"\n✓ Database updated: {csv_file}")
            print(f"  Total parts: {len(combined_df)}")
            print(f"  Toyota parts: {len(df)}")
            
            # Show price statistics
            print(f"\nToyota Price Statistics:")
            print(f"  Min: ${df['price'].min():.2f}")
            print(f"  Max: ${df['price'].max():.2f}")
            print(f"  Average: ${df['price'].mean():.2f}")
            print(f"  Median: ${df['price'].median():.2f}")
            
        except FileNotFoundError:
            # Create new file if it doesn't exist
            df.to_csv(csv_file, index=False)
            print(f"\n✓ Created new database: {csv_file}")
            print(f"  Total parts: {len(df)}")
    else:
        print("No parts to save.")
    
    print("\n" + "=" * 80)
    print("SCRAPING COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    scrape_all_toyota_parts()
