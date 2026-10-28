import sys
sys.stdout.reconfigure(encoding='utf-8')
import httpx
from bs4 import BeautifulSoup
import urllib.parse

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
}

q = 'محمد صلاح ابراهيم جامعة الانبار'
print("Testing lite.duckduckgo.com...")
try:
    r = httpx.post('https://lite.duckduckgo.com/lite/', data={'q': q}, headers=headers, timeout=8.0)
    print("Lite status:", r.status_code)
    soup = BeautifulSoup(r.text, 'html.parser')
    for a in soup.select('a.result-link'):
        print("  Found:", a.get_text(strip=True)[:60], "-->", a.get('href'))
except Exception as e:
    print("Lite error:", e)

print("\nTesting html.duckduckgo.com...")
try:
    r = httpx.post('https://html.duckduckgo.com/html/', data={'q': q}, headers=headers, timeout=8.0)
    print("HTML status:", r.status_code)
    soup = BeautifulSoup(r.text, 'html.parser')
    for a in soup.select('.result__title a'):
        print("  Found:", a.get_text(strip=True)[:60], "-->", a.get('href'))
except Exception as e:
    print("HTML error:", e)
