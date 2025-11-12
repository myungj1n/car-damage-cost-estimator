"""
VW Official Parts Site Scraper
Note: This site appears to have Cloudflare protection which blocks automated requests.
Alternative approach: Try with cloudscraper library which can bypass some protections.
"""

import pandas as pd

try:
    import cloudscraper
    print("Using cloudscraper to bypass Cloudflare protection...")
    scraper = cloudscraper.create_scraper()
except ImportError:
    print("cloudscraper not available. Installing...")
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "cloudscraper"])
    import cloudscraper
    print("cloudscraper installed successfully!")
    scraper = cloudscraper.create_scraper()

from bs4 import BeautifulSoup
import time

url = 'https://parts.vw.com/'

print(f"\nAttempting to access: {url}")
print("="*60)

try:
    response = scraper.get(url, timeout=30)
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        print(f"Page title: {soup.title.string if soup.title else 'No title'}")
        print()
        
        # Look for parts or products
        products = []
        
        # Try multiple patterns for finding products
        # Pattern 1: Products with data attributes
        parts_with_data = soup.find_all(['div', 'button', 'a'], attrs={'data-sku': True})
        print(f"Found {len(parts_with_data)} items with SKU data")
        
        for item in parts_with_data:
            sku = item.get('data-sku', 'N/A')
            name = item.get('data-name', item.get_text(strip=True)[:100])
            price_str = item.get('data-price', item.get('data-sale-price', '0'))
            
            try:
                price = float(price_str)
            except:
                price = 0.0
            
            products.append({
                'make': 'VOLKSWAGEN',
                'brand': 'Volkswagen',
                'part_name': name,
                'part_number': sku,
                'price': price,
                'url': url
            })
        
        # Pattern 2: Product cards or listings
        product_cards = soup.find_all(['div', 'article'], class_=lambda x: x and ('product' in x.lower() or 'item' in x.lower()))
        print(f"Found {len(product_cards)} product cards")
        
        # Pattern 3: Links to parts
        catalog_links = soup.find_all('a', href=True)
        parts_links = [link for link in catalog_links if any(keyword in link['href'].lower() for keyword in ['part', 'catalog', 'shop', 'product'])]
        print(f"Found {len(parts_links)} potential catalog links")
        
        if products:
            print(f"\n✅ Successfully scraped {len(products)} parts from VW site")
            df = pd.DataFrame(products)
            
            # Load existing data and append
            existing_df = pd.read_csv('oem_parts_data.csv')
            
            # Remove old VW entries (only 6 parts)
            existing_df = existing_df[existing_df['make'] != 'VOLKSWAGEN']
            
            # Append new data
            combined_df = pd.concat([existing_df, df], ignore_index=True)
            combined_df.to_csv('oem_parts_data.csv', index=False)
            
            print(f"Updated database: {len(combined_df)} total parts")
            print(f"VW parts: {len(df)}")
        else:
            print("\n⚠️ No products found. Site may require JavaScript or has strong protection.")
            print("\nTo get VW parts data, you may need to:")
            print("1. Use Selenium/Playwright for browser automation")
            print("2. Manually export data from the website")
            print("3. Contact VW for API access")
            
    else:
        print(f"❌ Failed to access site (Status: {response.status_code})")
        print("Site has Cloudflare protection that blocks automated access.")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nThe VW parts site has strong bot protection.")
    print("Current VW data (6 parts from vw.oempartsonline.com) will remain in database.")
