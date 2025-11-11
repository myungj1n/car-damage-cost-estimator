import requests
from bs4 import BeautifulSoup
import time

# Mapping of make names to their subdomain names
make_url_map = {
    'acura': 'acura',
    'honda': 'honda',
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

def get_category_links(base_url, make):
    """Get all category links from the homepage"""
    try:
        response = requests.get(base_url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        links = soup.find_all('a', href=True)
        categories = set()
        
        for link in links:
            href = link.get('href', '')
            if href and not href.startswith('http') and '/' in href:
                parts = href.strip('/').split('/')
                if len(parts) == 1 and len(parts[0]) > 3:
                    if not any(skip in href.lower() for skip in ['javascript', 'search', 'cart', 'account', 'contact', 'about', 'reviews', 'oem-parts']):
                        categories.add(href.strip('/'))
        
        return list(categories)
    except Exception as e:
        print(f"  ✗ Error getting categories: {e}")
        return []

def scrape_parts_from_page(url, make):
    """Scrape all parts from a single page"""
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        parts_data = []
        product_divs = soup.find_all('div', attrs={'data-sku': True})
        
        for div in product_divs:
            part_info = {
                'make': make,
                'brand': div.get('data-brand', make),
                'part_name': div.get('data-name', 'N/A'),
                'part_number': div.get('data-sku', 'N/A'),
                'price': div.get('data-price', 'N/A'),
            }
            
            link = div.find('a', href=True)
            if link:
                href = link.get('href', '')
                if href.startswith('http'):
                    part_info['url'] = href
                else:
                    part_info['url'] = url.rsplit('/', 1)[0] + '/' + href.lstrip('/')
            else:
                part_info['url'] = 'N/A'
            
            parts_data.append(part_info)
        
        return parts_data
        
    except Exception as e:
        print(f"    ✗ Error scraping page: {e}")
        return []

# Test with Honda
make = 'HONDA'
subdomain = 'honda'
base_url = f"https://{subdomain}.oempartsonline.com"

print(f"Testing comprehensive scraping for: {make}")
print(f"URL: {base_url}\n")

all_parts = []

# Homepage
print("1. Scraping homepage...")
homepage_parts = scrape_parts_from_page(base_url, make)
all_parts.extend(homepage_parts)
print(f"   ✓ Homepage: {len(homepage_parts)} parts\n")

# Categories
print("2. Finding categories...")
categories = get_category_links(base_url, make)
print(f"   ✓ Found {len(categories)} categories:")
for cat in categories[:10]:
    print(f"     - {cat}")
if len(categories) > 10:
    print(f"     ... and {len(categories) - 10} more\n")

# Scrape first 3 categories as test
print("\n3. Scraping first 3 categories as test:")
for i, category in enumerate(categories[:3], 1):
    category_url = f"{base_url}/{category}"
    print(f"   [{i}/3] {category}...", end=' ')
    
    category_parts = scrape_parts_from_page(category_url, make)
    all_parts.extend(category_parts)
    print(f"{len(category_parts)} parts")
    time.sleep(0.5)

# Remove duplicates
seen = set()
unique_parts = []
for part in all_parts:
    pn = part['part_number']
    if pn != 'N/A' and pn not in seen:
        seen.add(pn)
        unique_parts.append(part)

print(f"\n{'='*60}")
print(f"TEST RESULTS:")
print(f"  Total parts scraped: {len(all_parts)}")
print(f"  Unique parts: {len(unique_parts)}")
print(f"\nSample parts:")
for part in unique_parts[:5]:
    print(f"  - {part['part_name'][:40]:40} | ${part['price']:>8} | {part['part_number']}")
