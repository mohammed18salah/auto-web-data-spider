import requests
from bs4 import BeautifulSoup
import urllib.parse
import sys
sys.stdout.reconfigure(encoding='utf-8')

# Test different User-Agents and query formats for Google
variants = [
    ("Old Firefox", {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1'}),
    ("Lynx / Text", {'User-Agent': 'Lynx/2.8.8pre.4 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.12.23'}),
    ("Googlebot", {'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'}),
    ("Standard Chrome", {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'}),
]

query = 'محمد صلاح ابراهيم جامعة الانبار'

for label, h in variants:
    try:
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&hl=ar"
        r = requests.get(url, headers=h, timeout=4)
        soup = BeautifulSoup(r.text, 'html.parser')
        links = []
        for a in soup.select('a[href]'):
            href = a['href']
            if '/url?q=' in href:
                u = href.split('/url?q=')[1].split('&')[0]
                if u.startswith('http') and 'google.' not in u:
                    links.append((a.get_text(strip=True)[:40], u))
        print(f"{label}: Status {r.status_code}, Length {len(r.text)}, Links: {len(links)}")
        for t, u in links[:3]:
            print("  ", t, "-->", u[:70])
    except Exception as e:
        print(f"{label} error:", e)
