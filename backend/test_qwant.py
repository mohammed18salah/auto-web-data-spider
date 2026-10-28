import requests
import sys
sys.stdout.reconfigure(encoding='utf-8')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'ar,en;q=0.9',
}

query = 'محمد صلاح ابراهيم جامعة الانبار'

# Test Qwant
try:
    r = requests.get(
        'https://api.qwant.com/v3/search/web',
        params={'q': query, 'count': 10, 'locale': 'ar_aa'},
        headers=headers,
        timeout=5
    )
    print("Qwant status:", r.status_code)
    data = r.json()
    items = data.get('data', {}).get('result', {}).get('items', {}).get('mainline', [])
    print("Qwant items:", len(items))
    for it in items[:3]:
        for res in it.get('items', []):
            print("  Qwant title:", res.get('title'))
            print("  Qwant url:", res.get('url'))
except Exception as e:
    print("Qwant error:", e)

# Test Swisscows
try:
    r = requests.get(
        'https://api.swisscows.com/web/search',
        params={'query': query, 'page': 1, 'itemsCount': 10, 'region': 'iv'},
        headers=headers,
        timeout=5
    )
    print("Swisscows status:", r.status_code)
    data = r.json()
    for item in data.get('items', [])[:3]:
        print("  Swisscows:", item.get('title'), "-->", item.get('url'))
except Exception as e:
    print("Swisscows error:", e)
