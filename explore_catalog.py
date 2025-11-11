import requests
from bs4 import BeautifulSoup
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
}

# Test with Honda to understand catalog structure
url = "https://honda.oempartsonline.com"
print(f"Exploring: {url}\n")

response = requests.get(url, headers=headers, timeout=15)
soup = BeautifulSoup(response.content, 'html.parser')

# Look for category links
print("=== Looking for catalog/category links ===")
links = soup.find_all('a', href=True)

category_links = []
for link in links:
    href = link.get('href', '')
    text = link.get_text(strip=True)
    
    # Look for category/catalog patterns
    if any(pattern in href.lower() for pattern in ['category', 'catalog', 'parts', 'accessories', 'oem-parts']):
        if text and len(text) < 100:
            category_links.append((text, href))

# Remove duplicates
seen = set()
unique_categories = []
for text, href in category_links:
    if href not in seen:
        seen.add(href)
        unique_categories.append((text, href))

print(f"\nFound {len(unique_categories)} potential category links:")
for i, (text, href) in enumerate(unique_categories[:20], 1):
    print(f"{i:2}. {text[:50]:50} -> {href[:80]}")

# Check if there's a sitemap or parts listing page
print("\n\n=== Checking for sitemap or parts catalog ===")
sitemap_urls = [
    f"{url}/sitemap",
    f"{url}/catalog", 
    f"{url}/parts",
    f"{url}/all-parts",
    f"{url}/oem-parts"
]

for test_url in sitemap_urls:
    try:
        resp = requests.get(test_url, headers=headers, timeout=10)
        if resp.status_code == 200:
            print(f"✓ Found: {test_url}")
    except:
        pass
