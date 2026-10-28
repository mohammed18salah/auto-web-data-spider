import requests
import sys
sys.stdout.reconfigure(encoding='utf-8')

test_urls = [
    ("Google", "https://www.google.com/"),
    ("Bing", "https://www.bing.com/"),
    ("DuckDuckGo", "https://html.duckduckgo.com/html/"),
    ("Wikipedia API", "https://ar.wikipedia.org/w/api.php?action=query&list=search&srsearch=test&format=json"),
    ("Startpage", "https://www.startpage.com/"),
]

for name, url in test_urls:
    try:
        r = requests.get(url, timeout=3.5, headers={'User-Agent': 'Mozilla/5.0'})
        print(f"{name}: SUCCESS (status {r.status_code})")
    except Exception as e:
        print(f"{name}: FAILED ({type(e).__name__})")
