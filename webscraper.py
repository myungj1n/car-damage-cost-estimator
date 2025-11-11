import kagglehub
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import os

# Mapping of make names to their subdomain names (case-insensitive matching)
make_url_map = {
    'acura': 'acura',
    'audi': 'audi',
    'bmw': 'bmw',
    'ford': 'ford',
    'gm': 'g',
    'general motors': 'g',
    'chevrolet': 'g',
    'gmc': 'g',
    'buick': 'g',
    'cadillac': 'g',
    'honda': 'honda',
    'hyundai': 'hyundai',
    'infiniti': 'infiniti',
    'jaguar': 'jaguar',
    'kia': 'kia',
    'land rover': 'landrover',
    'lexus': 'lexus',
    'mazda': 'mazda',
    'mitsubishi': 'mitsubishi',
    'mopar': 'mopar',
    'dodge': 'mopar',
    'chrysler': 'mopar',
    'jeep': 'mopar',
    'ram': 'mopar',
    'nissan': 'nissan',
    'porsche': 'porsche',
    'subaru': 'subaru',
    'toyota': 'toyota',
    'volkswagen': 'vw',
    'vw': 'vw',
    'volvo': 'volvo'
}

# Download the dataset
path = kagglehub.dataset_download("natelee2003/vinapi")

# Load the dataset
print(f"Dataset downloaded to: {path}")
csv_files = [f for f in os.listdir(path) if f.endswith('.csv')]
print(f"Found CSV files: {csv_files}")

# Load the first CSV file (adjust if needed)
df = pd.read_csv(os.path.join(path, csv_files[0]), sep='\t')

# Display dataset info
print(f"\nDataset shape: {df.shape}")
print(f"\nColumn names: {df.columns.tolist()}")
print(f"\nFirst few rows:")
print(df.head())

# Extract unique car makes from the dataset
# The column is named 'MAKE' in uppercase based on the data
make_column = 'MAKE'
unique_makes = df[make_column].dropna().unique()

# Clean up the makes - remove quotes, trim whitespace, filter invalid entries
cleaned_makes = []
for make in unique_makes:
    make_str = str(make).strip().strip('"').strip()
    # Only keep makes that are valid (letters, reasonable length)
    if make_str and len(make_str) > 1 and make_str.replace(' ', '').replace('-', '').isalpha():
        cleaned_makes.append(make_str)

unique_makes = sorted(list(set(cleaned_makes)))  # Remove duplicates and sort

# Filter to only include makes available on oempartsonline.com
available_makes_list = list(set(make_url_map.keys()))
filtered_makes = [make for make in unique_makes if make.lower() in available_makes_list]

print(f"\nFiltered to {len(filtered_makes)} makes that are available on oempartsonline.com:")
print(filtered_makes)

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
            href = link.get('href', '')
            # Look for category-like URLs (not oem-parts individual items)
            if href and not href.startswith('http') and '/' in href:
                # Filter for likely category pages
                parts = href.strip('/').split('/')
                if len(parts) == 1 and len(parts[0]) > 3:
                    # Single-level paths like "engine-parts", "floor-mats"
                    if not any(skip in href.lower() for skip in ['javascript', 'search', 'cart', 'account', 'contact', 'about', 'reviews', 'oem-parts']):
                        categories.add(href.strip('/'))
        
        return list(categories)
    except Exception as e:
        print(f"  ✗ Error getting categories: {e}")
        return []

def scrape_parts_from_page(url, make):
    """
    Scrape all parts from a single page
    """
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        parts_data = []
        
        # Method 1: Look for product divs with data attributes (featured products on homepage)
        product_divs = soup.find_all('div', attrs={'data-sku': True})
        
        for div in product_divs:
            part_info = {
                'make': make,
                'brand': div.get('data-brand', make),
                'part_name': div.get('data-name', 'N/A'),
                'part_number': div.get('data-sku', 'N/A'),
                'price': div.get('data-price', 'N/A'),
            }
            
            # Get URL if available
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
        
        # Method 2: Look for "Add to Cart" buttons with data attributes (category pages)
        add_to_cart_buttons = soup.find_all('button', attrs={'data-sku': True, 'data-sale-price': True})
        
        for button in add_to_cart_buttons:
            part_info = {
                'make': make,
                'brand': button.get('data-brand', make),
                'part_name': button.get('data-name', 'N/A'),
                'part_number': button.get('data-sku', 'N/A'),
                'price': button.get('data-sale-price', 'N/A'),
            }
            
            # Try to get the product URL from the page
            # Find the product link associated with this SKU
            sku_stripped = button.get('data-sku-stripped', '')
            if sku_stripped:
                link = soup.find('a', href=lambda x: x and sku_stripped in x)
                if link:
                    href = link.get('href', '')
                    if href.startswith('http'):
                        part_info['url'] = href
                    elif href.startswith('/'):
                        # Get base URL from current URL
                        base = url.split('/')[0] + '//' + url.split('/')[2]
                        part_info['url'] = base + href
                    else:
                        part_info['url'] = 'N/A'
                else:
                    part_info['url'] = 'N/A'
            else:
                part_info['url'] = 'N/A'
            
            parts_data.append(part_info)
        
        return parts_data
        
    except Exception as e:
        print(f"    ✗ Error scraping page {url}: {e}")
        return []

def scrape_category_with_pagination(category_url, make, base_url):
    """
    Scrape all parts from a category, handling pagination
    """
    all_parts = []
    page = 1
    max_pages = 20  # Safety limit to avoid infinite loops
    
    while page <= max_pages:
        # Add page parameter to URL
        if '?' in category_url:
            page_url = f"{category_url}&page={page}"
        else:
            page_url = f"{category_url}?page={page}"
        
        try:
            response = requests.get(page_url, headers=headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract parts from this page
            buttons = soup.find_all('button', attrs={'data-sku': True, 'data-sale-price': True})
            
            if not buttons:
                # No more parts on this page
                break
            
            for button in buttons:
                part_info = {
                    'make': make,
                    'brand': button.get('data-brand', make),
                    'part_name': button.get('data-name', 'N/A'),
                    'part_number': button.get('data-sku', 'N/A'),
                    'price': button.get('data-sale-price', 'N/A'),
                }
                
                # Try to get the product URL
                sku_stripped = button.get('data-sku-stripped', '')
                if sku_stripped:
                    link = soup.find('a', href=lambda x: x and sku_stripped in x)
                    if link:
                        href = link.get('href', '')
                        if href.startswith('http'):
                            part_info['url'] = href
                        elif href.startswith('/'):
                            part_info['url'] = base_url + href
                        else:
                            part_info['url'] = 'N/A'
                    else:
                        part_info['url'] = 'N/A'
                else:
                    part_info['url'] = 'N/A'
                
                all_parts.append(part_info)
            
            # Check if there's a next page
            next_page_link = soup.find('a', class_='pagination-link', attrs={'data-page': str(page + 1)})
            if not next_page_link:
                # No more pages
                break
            
            page += 1
            time.sleep(0.3)  # Small delay between pages
            
        except Exception as e:
            print(f"      ✗ Error on page {page}: {e}")
            break
    
    return all_parts

def scrape_make_parts(make):
    """
    Scrape ALL OEM parts for a specific car make
    """
    try:
        # Get the subdomain for this make
        make_lower = make.lower()
        subdomain = make_url_map.get(make_lower)
        
        if not subdomain:
            print(f"⚠ Skipping {make} - not available on oempartsonline.com")
            return []
        
        # Construct URL using subdomain
        base_url = f"https://{subdomain}.oempartsonline.com"
        
        print(f"\nScraping: {make}")
        print(f"URL: {base_url}")
        
        all_parts = []
        
        # First, get featured products from homepage
        homepage_parts = scrape_parts_from_page(base_url, make)
        all_parts.extend(homepage_parts)
        print(f"  ✓ Homepage: {len(homepage_parts)} parts")
        
        # Get all category links
        print(f"  → Finding categories...")
        categories = get_category_links(base_url, make)
        print(f"  ✓ Found {len(categories)} categories")
        
        # Scrape each category with pagination
        for i, category in enumerate(categories, 1):
            category_url = f"{base_url}/{category}"
            print(f"  [{i}/{len(categories)}] {category}...", end=' ', flush=True)
            
            category_parts = scrape_category_with_pagination(category_url, make, base_url)
            all_parts.extend(category_parts)
            print(f"{len(category_parts)} parts")
            
            # Small delay between categories
            time.sleep(0.5)
        
        # Remove duplicates based on part_number
        seen_part_numbers = set()
        unique_parts = []
        for part in all_parts:
            part_num = part['part_number']
            if part_num != 'N/A' and part_num not in seen_part_numbers:
                seen_part_numbers.add(part_num)
                unique_parts.append(part)
        
        print(f"✓ Total unique parts for {make}: {len(unique_parts)}")
        return unique_parts
        
    except requests.exceptions.HTTPError as e:
        print(f"✗ HTTP Error for {make}: {e}")
        return []
    except requests.exceptions.RequestException as e:
        print(f"✗ Error fetching {make}: {e}")
        return []
    except Exception as e:
        print(f"✗ Error parsing {make}: {e}")
        import traceback
        traceback.print_exc()
        return []

# Scrape parts for each make in the dataset
all_parts_data = []
successful_makes = 0
failed_makes = 0

print(f"\n{'='*70}")
print(f"Starting COMPREHENSIVE web scraping for {len(filtered_makes)} makes")
print(f"This will scrape ALL parts from each make's catalog")
print(f"{'='*70}\n")

# Process all filtered makes
for i, make in enumerate(filtered_makes, 1):
    print(f"\n{'='*70}")
    print(f"[{i}/{len(filtered_makes)}] Processing: {make}")
    print(f"{'='*70}")
    
    parts = scrape_make_parts(make)
    
    if parts:
        all_parts_data.extend(parts)
        successful_makes += 1
        print(f"✓ {make}: {len(parts)} parts collected (Total: {len(all_parts_data)})")
    else:
        failed_makes += 1
        print(f"✗ {make}: No parts collected")
    
    # Be respectful - add delay between makes
    if i < len(filtered_makes):
        print(f"\n⏱ Waiting 3 seconds before next make...")
        time.sleep(3)

print(f"\n{'='*60}")
print(f"Scraping Complete!")
print(f"{'='*60}")
print(f"✓ Successfully scraped: {successful_makes} makes")
print(f"✗ Failed/Unavailable: {failed_makes} makes")
print(f"Total parts collected: {len(all_parts_data)}")

# Save results to CSV
if all_parts_data:
    results_df = pd.DataFrame(all_parts_data)
    output_file = 'oem_parts_data.csv'
    results_df.to_csv(output_file, index=False)
    print(f"\n✓ Data saved to: {output_file}")
    print(f"\nSample of scraped data:")
    print(results_df.head())
    print(f"\nColumn names: {results_df.columns.tolist()}")
    print(f"\nData summary:")
    print(results_df.describe(include='all'))
else:
    print("\n⚠ No data was scraped.")
    print("This could mean:")
    print("  - The makes in your dataset are not available on oempartsonline.com")
    print("  - There was a network issue")
    print("  - The website structure has changed")
