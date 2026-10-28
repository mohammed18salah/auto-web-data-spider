import httpx
from bs4 import BeautifulSoup
import urllib.parse
import sys
sys.stdout.reconfigure(encoding='utf-8')

client = httpx.Client(
    headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
    },
    follow_redirects=True,
    timeout=8.0
)

# Step 1: visit duckduckgo.com to establish cookies
r1 = client.get('https://duckduckgo.com/')
print('DDG home status:', r1.status_code)

# Step 2: search html endpoint with GET or POST
r2 = client.post('https://html.duckduckgo.com/html/', data={'q': '"محمد صلاح ابراهيم" "جامعة الانبار"'})
print('DDG search status:', r2.status_code)

soup = BeautifulSoup(r2.text, 'html.parser')
results = []
for res in soup.select('.result'):
    t = res.select_one('.result__title a')
    s = res.select_one('.result__snippet')
    if t:
        href = t.get('href', '')
        if '/l/?uddg=' in href:
            u = urllib.parse.unquote(href.split('/l/?uddg=')[1].split('&')[0])
        else:
            u = href
        results.append((t.get_text(strip=True), u, s.get_text(strip=True) if s else ''))

print(f"Results: {len(results)}")
for title, url, snip in results[:5]:
    print(" ", title[:60], "-->", url)
    print("   Snippet:", snip[:80])
