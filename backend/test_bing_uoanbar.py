import requests
from bs4 import BeautifulSoup
import urllib.parse
import base64
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
}

def decode_bing_url(href):
    if "bing.com/ck/a?" in href and "u=" in href:
        try:
            m = re.search(r'[?&]u=([^&]+)', href)
            if m:
                raw_u = m.group(1)
                if raw_u.startswith('a1'):
                    raw_u = raw_u[2:]
                padded = raw_u + '=' * (-len(raw_u) % 4)
                return base64.urlsafe_b64decode(padded).decode('utf-8', errors='ignore')
        except Exception:
            pass
    return href

r = requests.get('https://www.bing.com/search?q=uoanbar.edu.iq&setlang=ar', headers=headers, timeout=5)
soup = BeautifulSoup(r.text, 'html.parser')
results = []
for li in soup.select('li.b_algo'):
    h2 = li.select_one('h2 a')
    snip = li.select_one('.b_caption p')
    if h2:
        title = h2.get_text(strip=True)
        url = decode_bing_url(h2.get('href', ''))
        results.append((title, url, snip.get_text(strip=True) if snip else ''))

print(f"Bing found {len(results)} for uoanbar.edu.iq:")
for t, u, s in results[:6]:
    print("  Title:", t[:50])
    print("  URL:", u)
    print("  Snippet:", s[:80])
    print()
