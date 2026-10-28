import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('google_out.html', encoding='utf-8') as f:
    text = f.read()

matches = re.findall(r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', text, re.IGNORECASE | re.DOTALL)
print("Total A tags in google_out.html:", len(matches))
for h, inner in matches:
    clean_inner = re.sub(r'<[^>]+>', '', inner).strip()
    if 'google.com' not in h and not h.startswith('/') and not h.startswith('#'):
        print("EXTERNAL:", clean_inner[:50], "-->", h[:70])
    elif clean_inner:
        print("INTERNAL/RELATIVE:", clean_inner[:40], "-->", h[:50])
