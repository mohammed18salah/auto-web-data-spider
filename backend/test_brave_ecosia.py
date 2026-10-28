import requests
from bs4 import BeautifulSoup
import sys
sys.stdout.reconfigure(encoding='utf-8')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
}

query = 'محمد صلاح ابراهيم جامعة الانبار'

# Test Ecosia
try:
    r = requests.get('https://www.ecosia.org/search', params={'q': query}, headers=headers, timeout=6)
    print("Ecosia status:", r.status_code)
    soup = BeautifulSoup(r.text, 'html.parser')
    res = soup.select('a[data-test-id="result-link"], .result__title a')
    print("Ecosia results:", len(res))
    for a in res[:3]:
        print("  Ecosia:", a.get_text(strip=True)[:50], "-->", a.get('href'))
except Exception as e:
    print("Ecosia error:", e)

# Test Brave Search
try:
    r = requests.get('https://search.brave.com/search', params={'q': query}, headers=headers, timeout=6)
    print("Brave status:", r.status_code)
    soup = BeautifulSoup(r.text, 'html.parser')
    res = soup.select('.snippet[data-type="web"]')
    print("Brave results:", len(res))
    for s in res[:3]:
        t = s.select_one('.title')
        a = s.select_one('a')
        if t and a:
            print("  Brave:", t.get_text(strip=True)[:50], "-->", a.get('href'))
except Exception as e:
    print("Brave error:", e)
