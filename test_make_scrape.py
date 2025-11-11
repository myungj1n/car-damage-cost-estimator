import requests
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

# Test with Honda
url = "https://honda.oempartsonline.com"
print(f"Testing scrape of: {url}\n")

try:
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Print page title
    title = soup.find('title')
    print(f"Page title: {title.text if title else 'No title'}\n")
    
    # Look for category/model links
    print("Looking for model/category links...")
    links = soup.find_all('a', href=True)
    
    model_links = []
    for link in links[:100]:
        href = link.get('href', '')
        text = link.get_text(strip=True)
        if text and 'model' in href.lower() or 'year' in href.lower() or 'category' in href.lower():
            print(f"  {text}: {href}")
            model_links.append((text, href))
    
    # Look for price elements
    print("\n\nLooking for price patterns...")
    price_patterns = ['$', 'price', 'cost', 'msrp']
    for pattern in price_patterns:
        elements = soup.find_all(text=lambda text: text and pattern in text.lower())
        if elements:
            print(f"\nFound elements containing '{pattern}':")
            for elem in elements[:5]:
                print(f"  {elem.strip()[:100]}")
    
    # Save HTML for manual inspection
    with open('honda_page.html', 'w', encoding='utf-8') as f:
        f.write(soup.prettify())
    print("\n\n✓ Full HTML saved to 'honda_page.html' for inspection")
    
except Exception as e:
    print(f"Error: {e}")
