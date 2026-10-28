import requests
import sys
sys.stdout.reconfigure(encoding='utf-8')

headers = {'User-Agent': 'KnowledgeSpider/1.0 (mailto:dev@dataspider.local)'}
query = 'محمد صلاح ابراهيم جامعة الانبار'

# Test Crossref
try:
    url = f"https://api.crossref.org/works?query={query}&rows=5"
    r = requests.get(url, headers=headers, timeout=5)
    print("Crossref status:", r.status_code)
    data = r.json()
    items = data.get('message', {}).get('items', [])
    print(f"Crossref items: {len(items)}")
    for it in items[:3]:
        print("  Title:", it.get('title', ['No title'])[0][:60])
        print("  URL:", it.get('URL'))
except Exception as e:
    print("Crossref error:", e)

# Test OpenAlex
try:
    url = f"https://api.openalex.org/works?search={query}&per_page=5"
    r = requests.get(url, headers=headers, timeout=5)
    print("\nOpenAlex status:", r.status_code)
    data = r.json()
    results = data.get('results', [])
    print(f"OpenAlex results: {len(results)}")
    for res in results[:3]:
        print("  Title:", res.get('title', 'No title')[:60])
        print("  URL:", res.get('doi') or res.get('id'))
except Exception as e:
    print("OpenAlex error:", e)
