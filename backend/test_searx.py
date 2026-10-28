import requests
import sys
sys.stdout.reconfigure(encoding='utf-8')

instances = [
    "https://searx.be",
    "https://paulgo.io",
    "https://search.ononoki.org",
    "https://searx.work",
    "https://priv.au"
]

query = "محمد صلاح ابراهيم جامعة الانبار"

for inst in instances:
    try:
        r = requests.get(
            f"{inst}/search",
            params={'q': query, 'format': 'json', 'language': 'ar'},
            headers={'User-Agent': 'Mozilla/5.0'},
            timeout=4
        )
        if r.status_code == 200:
            data = r.json()
            results = data.get('results', [])
            print(f"{inst}: SUCCESS ({len(results)} results)")
            for res in results[:3]:
                print("  ", res.get('title')[:50], "-->", res.get('url'))
            break
        else:
            print(f"{inst}: Status {r.status_code}")
    except Exception as e:
        print(f"{inst}: Error {type(e).__name__}")
