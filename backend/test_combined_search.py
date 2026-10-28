import requests
from bs4 import BeautifulSoup
import urllib.parse
import base64
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
}

def search_ddg_html(q):
    try:
        r = requests.post(
            'https://html.duckduckgo.com/html/',
            data={'q': q},
            headers=headers,
            timeout=5.0
        )
        if r.status_code != 200:
            return []
        soup = BeautifulSoup(r.text, 'html.parser')
        results = []
        for res in soup.select('.result'):
            t = res.select_one('.result__title a')
            s = res.select_one('.result__snippet')
            if t:
                href = t.get('href', '')
                actual_url = href
                if '/l/?uddg=' in href:
                    actual_url = urllib.parse.unquote(href.split('/l/?uddg=')[1].split('&')[0])
                if actual_url.startswith('http') and 'duckduckgo.com' not in actual_url:
                    results.append({
                        'title': t.get_text(strip=True),
                        'url': actual_url,
                        'snippet': s.get_text(strip=True) if s else ''
                    })
        return results
    except Exception as e:
        print(f"DDG error on [{q}]: {e}")
        return []

def search_bing_html(q):
    try:
        r = requests.get(
            f"https://www.bing.com/search?q={urllib.parse.quote(q)}&setlang=ar",
            headers=headers,
            timeout=5.0
        )
        if r.status_code != 200:
            return []
        soup = BeautifulSoup(r.text, 'html.parser')
        results = []
        for li in soup.select('li.b_algo'):
            h2 = li.select_one('h2 a')
            snip = li.select_one('.b_caption p')
            if h2:
                title = h2.get_text(strip=True)
                href = h2.get('href', '')
                actual_url = href
                if "bing.com/ck/a?" in href and "u=" in href:
                    try:
                        m = re.search(r'[?&]u=([^&]+)', href)
                        if m:
                            raw = m.group(1)[2:] if m.group(1).startswith('a1') else m.group(1)
                            padded = raw + '=' * (-len(raw) % 4)
                            actual_url = base64.urlsafe_b64decode(padded).decode('utf-8', errors='ignore')
                    except Exception:
                        pass
                if actual_url.startswith('http') and 'bing.com' not in actual_url:
                    results.append({
                        'title': title,
                        'url': actual_url,
                        'snippet': snip.get_text(strip=True) if snip else ''
                    })
        return results
    except Exception as e:
        print(f"Bing error on [{q}]: {e}")
        return []

queries = [
    'دكتور محمد صلاح ابراهيم جامعة الانبار',
    '"محمد صلاح ابراهيم" "جامعة الانبار"',
    'محمد صلاح ابراهيم الانبار'
]

print("Testing combined search...")
for q in queries:
    print(f"\n--- Query: {q} ---")
    ddg_res = search_ddg_html(q)
    print(f"DDG returned {len(ddg_res)} results")
    for r in ddg_res[:2]:
        print("  DDG:", r['title'][:50], "-->", r['url'])
    
    bing_res = search_bing_html(q)
    print(f"Bing returned {len(bing_res)} results")
    for r in bing_res[:2]:
        print("  Bing:", r['title'][:50], "-->", r['url'])
