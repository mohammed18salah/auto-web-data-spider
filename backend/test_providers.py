import requests
import sys
sys.stdout.reconfigure(encoding='utf-8')

providers = [
    ("Bing", "https://www.bing.com/search?q=test"),
    ("Mojeek", "https://www.mojeek.com/search?q=test"),
    ("Qwant", "https://www.qwant.com/"),
    ("Swisscows", "https://swisscows.com/"),
    ("Wikidata", "https://www.wikidata.org/w/api.php?action=wbsearchentities&search=test&language=ar&format=json"),
    ("Google", "https://www.google.com/"),
]

for name, url in providers:
    try:
        r = requests.get(url, timeout=3.5, headers={'User-Agent': 'Mozilla/5.0'})
        print(f"{name}: SUCCESS (status {r.status_code})")
    except Exception as e:
        print(f"{name}: FAILED ({type(e).__name__})")
