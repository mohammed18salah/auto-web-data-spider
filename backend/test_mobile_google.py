import requests
from bs4 import BeautifulSoup
import sys
sys.stdout.reconfigure(encoding='utf-8')

headers = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ar-EG,ar;q=0.9,en-US;q=0.8,en;q=0.7',
}

query = 'محمد صلاح ابراهيم جامعة الانبار'
r = requests.get(f'https://www.google.com/search?q={query}&hl=ar', headers=headers, timeout=6)
print("Mobile Google status:", r.status_code, "Length:", len(r.text))

soup = BeautifulSoup(r.text, 'html.parser')
results = []
for a in soup.select('a[href]'):
    href = a['href']
    # Check for /url?q=
    if '/url?q=' in href:
        u = href.split('/url?q=')[1].split('&')[0]
        if u.startswith('http') and 'google.' not in u:
            txt = a.get_text(strip=True)
            if txt:
                results.append((txt[:60], u))
    elif href.startswith('http') and 'google.' not in href:
        div = a.select_one('div[role="heading"], div.BNeawe')
        if div:
            results.append((div.get_text(strip=True)[:60], href))

print(f"Mobile Google results: {len(results)}")
for t, u in results[:8]:
    print(" ", t, "-->", u)
