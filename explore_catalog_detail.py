import requests
from bs4 import BeautifulSoup
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
}

# Test catalog page
catalog_url = "https://honda.oempartsonline.com/catalog"
print(f"Exploring catalog: {catalog_url}\n")

response = requests.get(catalog_url, headers=headers, timeout=15)
soup = BeautifulSoup(response.content, 'html.parser')

print("Page title:", soup.find('title').text if soup.find('title') else 'N/A')

# Look for model year selection or category listings
print("\n=== Looking for model/year selection ===")
selects = soup.find_all('select')
for select in selects[:5]:
    select_id = select.get('id', 'no-id')
    options = select.find_all('option')
    print(f"\nSelect: {select_id} ({len(options)} options)")
    for opt in options[:10]:
        print(f"  - {opt.get_text(strip=True)}")

# Look for category cards/links
print("\n\n=== Looking for category cards ===")
category_divs = soup.find_all('div', class_=lambda x: x and ('category' in x.lower() or 'card' in x.lower()))
print(f"Found {len(category_divs)} potential category divs")

# Check for links to parts
print("\n\n=== Looking for parts links ===")
links = soup.find_all('a', href=True)
oem_parts_links = [link for link in links if '/oem-parts/' in link.get('href', '')]
print(f"Found {len(oem_parts_links)} links to individual parts")

# Save the page for inspection
with open('catalog_page.html', 'w', encoding='utf-8') as f:
    f.write(soup.prettify())
print("\n✓ Saved catalog_page.html for inspection")

# Try to find API endpoints
print("\n\n=== Looking for API endpoints in page scripts ===")
scripts = soup.find_all('script')
for script in scripts:
    script_text = script.string
    if script_text and ('api' in script_text.lower() or 'ajax' in script_text.lower()):
        # Look for URLs
        urls = []
        import re
        url_pattern = r'https?://[^\s"\'>]+'
        urls = re.findall(url_pattern, script_text)
        if urls:
            print("Found URLs in scripts:")
            for url in urls[:10]:
                if 'parts' in url.lower() or 'api' in url.lower():
                    print(f"  - {url}")
