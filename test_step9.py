# -*- coding: utf-8 -*-
"""
Test: STEP 9 - crawler/parser.py
Run:  python test_step9.py
"""
import sys
sys.path.insert(0, ".")

from knowledge_spider.utils.logger import setup_logger
setup_logger("test_parser")

from knowledge_spider.core.config import get_config
from knowledge_spider.crawler.parser import parse_page, extract_outbound_links

cfg = get_config()

# Dummy HTML for testing
test_html = """
<!DOCTYPE html>
<html>
<head>
    <title>   KnowledgeSpider Test Page   </title>
    <meta name="description" content="This is a test description.">
    <style>body { color: red; }</style>
    <script>alert('spam');</script>
</head>
<body>
    <header>
        <nav><a href="/home">Home</a> | <a href="/about">About</a></nav>
    </header>
    
    <main>
        <h1>Main Content Area</h1>
        <p>This is the <b>important</b> text that we want to extract.</p>
        <a href="https://en.wikipedia.org/wiki/Spider">Wikipedia Link</a>
        <a href="https://untrusted.com/spam">Spam Link</a>
        <a href="#section2">Anchor Link</a>
    </main>
    
    <aside>
        <p>Sidebar ads and related links.</p>
    </aside>
    
    <footer>
        <p>&copy; 2026 Test Site. <a href="mailto:admin@test.com">Contact</a></p>
    </footer>
</body>
</html>
"""
test_url = "https://docs.python.org/3/tutorial/"

# ── Test 1: parse_page (Text & Metadata) ──────────────────────────────────────
parsed = parse_page(test_html, test_url)

assert parsed["title"] == "KnowledgeSpider Test Page"
assert parsed["meta_description"] == "This is a test description."
assert parsed["url"] == test_url
assert parsed["domain"] == "docs.python.org"

# Check noise removal
text = parsed["text"]
assert "Main Content Area" in text
assert "important text" in text
assert "alert('spam')" not in text        # Script removed
assert "body { color: red; }" not in text # Style removed
assert "Home | About" not in text         # Nav removed
assert "Sidebar ads" not in text          # Aside removed
assert "2026 Test Site" not in text       # Footer removed

print(f"[OK] parse_page: correctly extracted title, meta, domain")
print(f"[OK] parse_page: correctly stripped noise tags (scripts, nav, footer)")
print(f"[OK] parse_page: extracted clean text -> '{text[:50]}...' ({parsed['word_count']} words)")

# ── Test 2: extract_outbound_links (No filter) ────────────────────────────────
cfg.crawler.trusted_only = False
links_all = extract_outbound_links(test_html, test_url, cfg)

assert "https://docs.python.org/home" in links_all     # Relative resolved
assert "https://docs.python.org/about" in links_all    # Relative resolved
assert "https://en.wikipedia.org/wiki/Spider" in links_all
assert "https://untrusted.com/spam" in links_all

# Exclusions
assert "mailto:admin@test.com" not in links_all
assert "javascript:alert('spam')" not in links_all
assert test_url not in links_all                       # Self anchor link (#section2 resolves to base)

print(f"[OK] extract_outbound_links (no filter): found {len(links_all)} absolute URLs")
print(f"[OK] extract_outbound_links: correctly resolved relative URLs")
print(f"[OK] extract_outbound_links: correctly excluded mailto/javascript/self links")

# ── Test 3: extract_outbound_links (trusted_only=True) ────────────────────────
cfg.crawler.trusted_only = True
links_trusted = extract_outbound_links(test_html, test_url, cfg)

# Should contain relative links (same domain) and wikipedia
assert "https://docs.python.org/home" in links_trusted
assert "https://en.wikipedia.org/wiki/Spider" in links_trusted

# Should NOT contain untrusted.com
assert "https://untrusted.com/spam" not in links_trusted

print(f"[OK] extract_outbound_links (trusted_only): blocked untrusted.com, allowed wikipedia and same-domain")

print("\n=== STEP 9 COMPLETE: HTML Parser verified ===")
