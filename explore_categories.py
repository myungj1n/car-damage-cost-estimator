import requests
from bs4 import BeautifulSoup
import time

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
}

# Try different category pages
base_url = "https://honda.oempartsonline.com"
categories = [
    "engine-parts",
    "exterior-accessories", 
    "interior-accessories",
    "floor-mats",
    "roof-racks"
]

for category in categories[:2]:  # Test first 2
    url = f"{base_url}/{category}"
    print(f"\n{'='*60}")
    print(f"Testing: {url}")
    print('='*60)
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        title = soup.find('title')
        print(f"Title: {title.text if title else 'N/A'}")
        
        # Look for product listings
        products = soup.find_all('div', class_=lambda x: x and 'product' in x.lower())
        print(f"Found {len(products)} product divs")
        
        # Look for parts with prices
        prices = soup.find_all(text=lambda text: text and '$' in text)
        price_count = len([p for p in prices if p.strip().startswith('$')])
        print(f"Found {price_count} prices on page")
        
        # Look for pagination
        pagination = soup.find_all('a', href=True, text=lambda t: t and ('next' in t.lower() or 'page' in t.lower()))
        print(f"Found {len(pagination)} pagination links")
        
        # Get all part links
        part_links = [a.get('href') for a in soup.find_all('a', href=True) if '/oem-parts/' in a.get('href', '')]
        print(f"Found {len(part_links)} parts on this category page")
        
        if part_links:
            print(f"\nSample part links:")
            for link in part_links[:3]:
                print(f"  - {link}")
        
        time.sleep(1)
        
    except Exception as e:
        print(f"Error: {e}")
