import requests
from bs4 import BeautifulSoup
import sys
sys.stdout.reconfigure(encoding='utf-8')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'ar,en;q=0.9',
}

query = 'محمد صلاح ابراهيم جامعة الانبار'
try:
    r = requests.get('https://yandex.com/search/', params={'text': query}, headers=headers, timeout=5)
    print("Yandex status:", r.status_code)
    soup = BeautifulSoup(r.text, 'html.parser')
    res = []
    for a in soup.select('a.organic__url, a.Link_theme_normal'):
        h = a.get('href')
        if h and h.startswith('http') and 'yandex.' not in h:
            res.append((a.get_text(strip=True)[:50], h))
    print(f"Yandex results: {len(res)}")
    for t, u in res[:5]:
        print(" ", t, "-->", u)
except Exception as e:
    print("Yandex error:", e)
