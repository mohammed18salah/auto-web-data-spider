import re

with open('google_out.html', encoding='utf-8') as f:
    html = f.read()

print("HTML length:", len(html))
links = re.findall(r'href=[\'"](https?://[^\'">]+)[\'"]', html)
external = [l for l in links if 'google.' not in l and 'gstatic.' not in l and 'w3.org' not in l]
print(f"External links found: {len(external)}")
for l in set(external):
    print("  ", l)
