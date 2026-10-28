import requests
from bs4 import BeautifulSoup
import sys
sys.stdout.reconfigure(encoding='utf-8')

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'}
r = requests.get('https://www.google.com/search?q=uoanbar&hl=ar', headers=headers)
soup = BeautifulSoup(r.text, 'html.parser')

print("All elements with data-href or href:")
for a in soup.find_all('a'):
    h = a.get('href', '')
    if 'uoanbar' in h or 'edu.iq' in h:
        print("MATCHED A:", a.get_text(strip=True)[:40], "-->", h)

for div in soup.find_all(['div', 'span']):
    dh = div.get('data-href', '')
    if 'uoanbar' in dh or 'edu.iq' in dh:
        print("MATCHED DIV:", div.get_text(strip=True)[:40], "-->", dh)
