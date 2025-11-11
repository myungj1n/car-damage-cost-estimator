import requests
from bs4 import BeautifulSoup

# Headers to mimic a browser
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

# Test with the main page first
url = "https://oempartsonline.com"
print(f"Inspecting: {url}\n")

try:
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Print page title
    title = soup.find('title')
    print(f"Page title: {title.text if title else 'No title'}\n")
    
    # Look for links to different car makes
    print("Looking for car make links...")
    links = soup.find_all('a', href=True)
    
    # Filter for potential make links
    make_links = []
    for link in links[:50]:  # Check first 50 links
        href = link.get('href', '')
        text = link.get_text(strip=True)
        if text and len(text) < 30:  # Car makes are usually short
            print(f"  {text}: {href}")
            make_links.append((text, href))
    
    print(f"\n\nFound {len(make_links)} potential links")
    
    # Save HTML for inspection
    with open('site_structure.html', 'w', encoding='utf-8') as f:
        f.write(soup.prettify())
    print("\n✓ Full HTML saved to 'site_structure.html' for inspection")
    
except Exception as e:
    print(f"Error: {e}")
