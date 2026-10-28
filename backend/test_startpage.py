import requests
from bs4 import BeautifulSoup
import sys
sys.stdout.reconfigure(encoding='utf-8')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'ar,en;q=0.9',
}

# Startpage search (Startpage proxies Google!)
try:
    r = requests.post(
        'https://www.startpage.com/sp/search',
        data={'query': 'محمد صلاح ابراهيم جامعة الانبار'},
        headers=headers,
        timeout=8
    )
    print("Startpage status:", r.status_code)
    soup = BeautifulSoup(r.text, 'html.parser')
    for a in soup.select('a.result-title'):
        print("Startpage:", a.get_text(strip=True)[:50], "-->", a.get('href'))
except Exception as e:
    print("Startpage error:", e)

# Test Yahoo
try:
    r = requests.get(
        'https://search.yahoo.com/search',
        params={'p': 'محمد صلاح ابراهيم جامعة الانبار'},
        headers=headers,
        timeout=8
    )
    print("Yahoo status:", r.status_code)
    soup = BeautifulSoup(r.text, 'html.parser')
    for h3 in soup.select('h3 a'):
        print("Yahoo:", h3.get_text(strip=True)[:50], "-->", h3.get('href'))
except Exception as e:
    print("Yahoo error:", e)
