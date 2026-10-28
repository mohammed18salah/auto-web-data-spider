import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
import sys
sys.stdout.reconfigure(encoding='utf-8')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'ar,en;q=0.9',
}

query = 'محمد صلاح ابراهيم جامعة الانبار'

# Test Yahoo
try:
    url = f"https://search.yahoo.com/search?p={urllib.parse.quote(query)}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=6) as resp:
        soup = BeautifulSoup(resp.read(), 'html.parser')
        results = []
        for h3 in soup.select('h3.title a'):
            results.append((h3.get_text(strip=True), h3.get('href')))
        print(f"Yahoo: {len(results)} results")
        for t, u in results[:3]:
            print("  ", t[:50], "->", u[:70])
except Exception as e:
    print("Yahoo error:", e)

# Test Bing
try:
    url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}&setlang=ar"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=6) as resp:
        soup = BeautifulSoup(resp.read(), 'html.parser')
        results = []
        for h2 in soup.select('li.b_algo h2 a'):
            results.append((h2.get_text(strip=True), h2.get('href')))
        print(f"Bing: {len(results)} results")
        for t, u in results[:3]:
            print("  ", t[:50], "->", u[:70])
except Exception as e:
    print("Bing error:", e)
