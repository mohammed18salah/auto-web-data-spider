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

def search_bing(query):
    url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}&setlang=ar"
    r = requests.get(url, headers=headers, timeout=5)
    soup = BeautifulSoup(r.text, 'html.parser')
    results = []
    for li in soup.select('li.b_algo'):
        h2 = li.select_one('h2 a')
        snip = li.select_one('.b_caption p')
        if h2:
            title = h2.get_text(strip=True)
            href = h2.get('href', '')
            actual_url = href
            if "bing.com/ck/a?" in href and "u=" in href:
                try:
                    match = re.search(r'[?&]u=([^&]+)', href)
                    if match:
                        raw_u = match.group(1)
                        if raw_u.startswith('a1'):
                            raw_u = raw_u[2:]
                        padded = raw_u + '=' * (-len(raw_u) % 4)
                        actual_url = base64.urlsafe_b64decode(padded).decode('utf-8', errors='ignore')
                except Exception:
                    pass
            results.append({
                'title': title,
                'url': actual_url,
                'snippet': snip.get_text(strip=True) if snip else ''
            })
    return results

test_queries = [
    'محمد صلاح ابراهيم جامعة الانبار',
    'محمد صلاح جامعة الانبار',
    'جامعة الانبار محمد صلاح',
    'uoanbar.edu.iq محمد صلاح',
    'كلية الحاسوب جامعة الانبار محمد صلاح',
    'محمد صلاح ابراهيم حاسبات الانبار'
]

for q in test_queries:
    res = search_bing(q)
    print(f"\nQuery: [{q}] -> Found {len(res)} results:")
    for r in res[:2]:
        print(" ", r['title'][:60], "-->", r['url'])
        if r['snippet']:
            print("   Snip:", r['snippet'][:80])
