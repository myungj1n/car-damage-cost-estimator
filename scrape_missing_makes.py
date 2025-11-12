import pandas as pd
import requests
from bs4 import BeautifulSoup
import time

# URLs for the missing makes
missing_makes_urls = {
    'TOYOTA': 'https://toyota.oempartsonline.com',
    'VOLKSWAGEN': 'https://vw.oempartsonline.com',
    'VOLVO': 'https://volvo.oempartsonline.com'
}

# Headers to mimic a browser
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

def get_category_links(base_url, make):
    """
    Get all category links from the homepage
    """
    try:
        response = requests.get(base_url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all category links
        links = soup.find_all('a', href=True)
        categories = set()
        
        for link in links:
            href = link['href']
            # Look for catalog URLs (they typically contain /a/ for categories)
            if '/a/' in href and base_url in href:
                categories.add(href)
        
        print(f"  Found {len(categories)} category links for {make}")
        return list(categories)
    except Exception as e:
        print(f"  Error getting categories for {make}: {e}")
        return []

def scrape_category_with_pagination(category_url, make, brand):
    """
    Scrape all parts from a category page, handling pagination
    """
    parts = []
    page_num = 1
    current_url = category_url
    
    while current_url:
        try:
            print(f"    Scraping page {page_num} of {category_url.split('/')[-1][:30]}...")
            response = requests.get(current_url, headers=headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all parts - try multiple patterns
            # Pattern 1: Featured products on homepage (div with data attributes)
            featured_products = soup.find_all('div', attrs={'data-sku': True, 'data-name': True})
            for product in featured_products:
                sku = product.get('data-sku', 'N/A')
                name = product.get('data-name', 'N/A')
                price_str = product.get('data-sale-price', product.get('data-price', '0'))
                
                try:
                    price = float(price_str) if price_str else 0.0
                except:
                    price = 0.0
                
                # Get the URL from the parent link
                parent_link = product.find_parent('a')
                url = parent_link['href'] if parent_link and parent_link.get('href') else 'N/A'
                if url != 'N/A' and not url.startswith('http'):
                    url = category_url.split('/a/')[0] + url
                
                parts.append({
                    'make': make,
                    'brand': brand,
                    'part_name': name,
                    'part_number': sku,
                    'price': price,
                    'url': url
                })
            
            # Pattern 2: Category page products (button elements)
            buttons = soup.find_all('button', attrs={'data-sku': True})
            for button in buttons:
                sku = button.get('data-sku', 'N/A')
                name = button.get('data-name', 'N/A')
                price_str = button.get('data-sale-price', button.get('data-price', '0'))
                
                try:
                    price = float(price_str) if price_str else 0.0
                except:
                    price = 0.0
                
                # Try to find the product URL
                product_card = button.find_parent('div', class_='card')
                url = 'N/A'
                if product_card:
                    link = product_card.find('a', href=True)
                    if link:
                        url = link['href']
                        if not url.startswith('http'):
                            url = category_url.split('/a/')[0] + url
                
                parts.append({
                    'make': make,
                    'brand': brand,
                    'part_name': name,
                    'part_number': sku,
                    'price': price,
                    'url': url
                })
            
            # Check for next page
            next_button = soup.find('a', {'aria-label': 'Next'}) or soup.find('a', string='Next')
            if next_button and next_button.get('href'):
                next_url = next_button['href']
                if not next_url.startswith('http'):
                    current_url = category_url.split('/a/')[0] + next_url
                else:
                    current_url = next_url
                page_num += 1
                time.sleep(1)  # Be polite with pagination
            else:
                current_url = None
                
        except Exception as e:
            print(f"    Error scraping category page {page_num}: {e}")
            current_url = None
    
    return parts

def scrape_make_parts(make, base_url):
    """
    Scrape all parts for a given make
    """
    print(f"\nScraping {make}...")
    print(f"  Base URL: {base_url}")
    
    all_parts = []
    brand = make.title()
    
    # First, scrape the homepage for featured products
    print(f"  Scraping homepage featured products...")
    try:
        response = requests.get(base_url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find featured products on homepage
        featured_products = soup.find_all('div', attrs={'data-sku': True, 'data-name': True})
        for product in featured_products:
            sku = product.get('data-sku', 'N/A')
            name = product.get('data-name', 'N/A')
            price_str = product.get('data-sale-price', product.get('data-price', '0'))
            
            try:
                price = float(price_str) if price_str else 0.0
            except:
                price = 0.0
            
            parent_link = product.find_parent('a')
            url = parent_link['href'] if parent_link and parent_link.get('href') else 'N/A'
            if url != 'N/A' and not url.startswith('http'):
                url = base_url + url
            
            all_parts.append({
                'make': make,
                'brand': brand,
                'part_name': name,
                'part_number': sku,
                'price': price,
                'url': url
            })
        
        print(f"  Found {len(featured_products)} featured products on homepage")
    except Exception as e:
        print(f"  Error scraping homepage: {e}")
    
    # Get all category links
    categories = get_category_links(base_url, make)
    
    # Scrape each category
    for i, category_url in enumerate(categories, 1):
        print(f"  Scraping category {i}/{len(categories)}...")
        category_parts = scrape_category_with_pagination(category_url, make, brand)
        all_parts.extend(category_parts)
        time.sleep(1)  # Be polite between categories
    
    print(f"  Total parts found for {make}: {len(all_parts)}")
    return all_parts

# Main scraping process
all_scraped_parts = []

for make, url in missing_makes_urls.items():
    parts = scrape_make_parts(make, url)
    all_scraped_parts.extend(parts)
    time.sleep(2)  # Be polite between makes

# Create DataFrame
new_df = pd.DataFrame(all_scraped_parts)

# Remove duplicates (same part_number for same make)
new_df = new_df.drop_duplicates(subset=['make', 'part_number'], keep='first')

print(f"\n{'='*60}")
print(f"SCRAPING COMPLETE")
print(f"{'='*60}")
print(f"Total new parts scraped: {len(new_df)}")
print(f"\nBreakdown by make:")
for make in new_df['make'].unique():
    count = len(new_df[new_df['make'] == make])
    print(f"  {make}: {count} parts")

# Load existing data
existing_df = pd.read_csv('oem_parts_data.csv')
print(f"\nExisting dataset: {len(existing_df)} parts")

# Append new data
combined_df = pd.concat([existing_df, new_df], ignore_index=True)
print(f"Combined dataset: {len(combined_df)} parts")

# Save the updated dataset
combined_df.to_csv('oem_parts_data.csv', index=False)
print(f"\n✅ Successfully updated oem_parts_data.csv with {len(new_df)} new parts!")
print(f"   Total parts in database: {len(combined_df)}")
print(f"   Total makes covered: {combined_df['make'].nunique()}")
