import requests
from bs4 import BeautifulSoup
import sys
sys.stdout.reconfigure(encoding='utf-8')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
    'Cookie': 'CONSENT=PENDING+987; SOCS=CAESEwgDEgk2MTQ5MTA1OTQaAmVuIAEaBgiA_LyaBg',
}

query = 'محمد صلاح ابراهيم جامعة الانبار'
r = requests.get(f'https://www.google.com/search?q={query}&hl=ar', headers=headers, timeout=6)
print("Google status:", r.status_code, "Length:", len(r.text))
soup = BeautifulSoup(r.text, 'html.parser')
results = []
for el in soup.select('div.g, div[data-hveid]'):
    h3 = el.select_one('h3')
    a = el.select_one('a[href^="http"]')
    if h3 and a:
        u = a['href']
        if 'google.com' not in u:
            results.append((h3.get_text(strip=True), u))

print(f"Google found: {len(results)}")
for t, u in results[:8]:
    print("  ", t[:50], "-->", u)
