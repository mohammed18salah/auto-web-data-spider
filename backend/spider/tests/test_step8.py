# -*- coding: utf-8 -*-
"""
Test: STEP 8 - crawler/fetcher.py
Run:  python test_step8.py
"""
import sys
sys.path.insert(0, ".")

from knowledge_spider.utils.logger import setup_logger
setup_logger("test_fetcher")

from knowledge_spider.core.config import get_config
from knowledge_spider.crawler.fetcher import fetch_page

cfg = get_config()
# Reduce delay for fast tests
cfg.crawler.crawl_delay_seconds = 0.5 

# ── Test 1: Successful fetch (HTML) ───────────────────────────────────────────
print("Fetching Wikipedia main page...")
result = fetch_page("https://en.wikipedia.org/wiki/Main_Page", cfg)

assert result is not None
assert result["status_code"] == 200
assert "html" in result
assert len(result["html"]) > 1000  # Must have some substantial HTML
assert "headers" in result
assert "fetched_at" in result
print(f"[OK] fetch_page: success (length={len(result['html'])} bytes)")

# ── Test 2: Redirects are followed ────────────────────────────────────────────
print("Fetching http URL that redirects to https...")
result_redir = fetch_page("http://wikipedia.org", cfg)
assert result_redir is not None
assert result_redir["url"].startswith("https://")
print(f"[OK] fetch_page: followed redirect to {result_redir['url']}")

# ── Test 3: 404 Not Found returns None ────────────────────────────────────────
print("Fetching non-existent page (expecting 404)...")
result_404 = fetch_page("https://en.wikipedia.org/wiki/ThisPageDoesNotExist123456789", cfg)
assert result_404 is None
print("[OK] fetch_page: gracefully returns None on 404")

# ── Test 4: Blocked by robots.txt returns None ────────────────────────────────
print("Fetching robots-blocked page...")
cfg.crawler.respect_robots = True
result_blocked = fetch_page("https://en.wikipedia.org/w/index.php?search=foo", cfg)
assert result_blocked is None
print("[OK] fetch_page: gracefully returns None for robots.txt blocked URL")

# ── Test 5: Non-HTML content returns None ─────────────────────────────────────
# We test against an image URL to verify Content-Type filtering
print("Fetching an image file (non-HTML)...")
result_img = fetch_page("https://upload.wikimedia.org/wikipedia/en/a/a9/Example.jpg", cfg)
assert result_img is None
print("[OK] fetch_page: gracefully returns None for non-HTML content (images)")

print("\n=== STEP 8 COMPLETE: Fetcher verified ===")
