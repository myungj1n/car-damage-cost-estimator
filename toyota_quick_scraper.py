"""
Quick Toyota Parts Scraper - Tests specific part categories
Targets high-value part categories relevant to body damage repair
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

# Focus on body/exterior parts relevant to damage repair
TARGET_PART_CATEGORIES = [
    'gas_cap',
    'emblem',
    'door_handle',
    'door_lock',
    'bumper',
    'fender',
    'hood',
    'headlight',
    'tail_light',
    'mirror',
    'grille',
    'windshield',
    'window',
    'quarter_panel',
    'rocker_panel'
]

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
            
            price_info = item.get('priceInfo', {})
            price = price_info.get('price', '0')
            
            part_url = item.get('url', '')
            if part_url and not part_url.startswith('http'):
                part_url = urljoin('https://www.toyotapartsdeal.com', part_url)
            
            if other_name:
                part_name = f"{description} - {other_name}"
            else:
                part_name = description
            
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
        except Exception:
            continue
    
    return parts

def scrape_part_category(category_name, retries=2):
    """Scrape a specific part category"""
    url = f'https://www.toyotapartsdeal.com/oem-toyota-{category_name}.html'
    
    for attempt in range(retries):
        try:
            proxies = get_rotating_proxy()
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            }
            
            response = requests.get(url, headers=headers, proxies=proxies, timeout=20)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                json_data = extract_json_from_page(soup)
                if json_data:
                    parts = extract_toyota_parts_from_json(json_data, url)
                    return parts
                else:
                    return []
            elif response.status_code == 404:
                # Part category doesn't exist
                return []
                
        except requests.Timeout:
            if attempt < retries - 1:
                time.sleep(1)
        except Exception:
            if attempt < retries - 1:
                time.sleep(1)
    
    return []

def scrape_target_parts():
    """Scrape all target part categories"""
    print("=" * 80)
    print("TOYOTA QUICK SCRAPER - BODY/EXTERIOR PARTS")
    print("=" * 80)
    print(f"\nTarget categories: {len(TARGET_PART_CATEGORIES)}")
    
    all_parts = []
    
    for idx, category in enumerate(TARGET_PART_CATEGORIES, 1):
        print(f"[{idx}/{len(TARGET_PART_CATEGORIES)}] {category}... ", end='', flush=True)
        
        parts = scrape_part_category(category)
        
        if parts:
            print(f"✓ {len(parts)} parts")
            all_parts.extend(parts)
        else:
            print("✗ no data")
        
        time.sleep(0.5)
    
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    print(f"Total parts scraped: {len(all_parts)}")
    
    if all_parts:
        df = pd.DataFrame(all_parts)
        df = df.drop_duplicates(subset=['part_number'], keep='first')
        df = df[df['price'] > 0]
        
        print(f"Unique valid parts: {len(df)}")
        
        # Update database
        csv_file = 'oem_parts_data.csv'
        
        try:
            existing_df = pd.read_csv(csv_file)
            print(f"\nExisting database: {len(existing_df)} parts")
            
            existing_df = existing_df[existing_df['make'] != 'Toyota']
            print(f"After removing old Toyota: {len(existing_df)} parts")
            
            combined_df = pd.concat([existing_df, df], ignore_index=True)
            combined_df.to_csv(csv_file, index=False)
            
            print(f"After adding new Toyota: {len(combined_df)} parts")
            print(f"\n✓ Database updated!")
            print(f"  Toyota parts: {len(df)}")
            print(f"  Price range: ${df['price'].min():.2f} - ${df['price'].max():.2f}")
            print(f"  Average price: ${df['price'].mean():.2f}")
            
        except FileNotFoundError:
            df.to_csv(csv_file, index=False)
            print(f"\n✓ Created new database with {len(df)} Toyota parts")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    scrape_target_parts()
