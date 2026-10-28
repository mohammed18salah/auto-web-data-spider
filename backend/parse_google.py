from bs4 import BeautifulSoup
import sys
sys.stdout.reconfigure(encoding='utf-8')

soup = BeautifulSoup(open('google_out.html', encoding='utf-8').read(), 'html.parser')
results = []
for a in soup.select('a[href]'):
    href = a['href']
    h3 = a.select_one('h3')
    if h3 and href.startswith('http') and not 'google.' in href:
        results.append((h3.get_text(strip=True), href))

print(f"Direct h3 links: {len(results)}")
for title, url in results[:10]:
    print(" ", title, "-->", url)

if len(results) == 0:
    for a in soup.select('a[href]'):
        href = a['href']
        if '/url?q=' in href:
            u = href.split('/url?q=')[1].split('&')[0]
            txt = a.get_text(strip=True)
            if txt and not 'google.' in u:
                print("  /url?q= link:", txt[:40], "-->", u)
