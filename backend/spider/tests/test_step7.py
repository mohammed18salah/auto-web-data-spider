# -*- coding: utf-8 -*-
"""
Test: STEP 7 - crawler/robots.py
Run:  python test_step7.py
"""
import sys
sys.path.insert(0, ".")

from knowledge_spider.utils.logger import setup_logger
setup_logger("test_robots")

from knowledge_spider.core.config import get_config
from knowledge_spider.crawler.robots import is_crawl_allowed, clear_robots_cache, _ROBOTS_CACHE

cfg = get_config()
clear_robots_cache()

# ── Test 1: Config toggle respects override ───────────────────────────────────
cfg.crawler.respect_robots = False
assert is_crawl_allowed("https://google.com/search") is True
print("[OK] is_crawl_allowed: returns True immediately if respect_robots=False")
assert len(_ROBOTS_CACHE) == 0

# ── Test 2: Standard allowed URL ──────────────────────────────────────────────
cfg.crawler.respect_robots = True
url_allowed = "https://en.wikipedia.org/wiki/Main_Page"
assert is_crawl_allowed(url_allowed) is True
print("[OK] is_crawl_allowed: allows standard Wikipedia page")

# ── Test 3: Caching works ─────────────────────────────────────────────────────
# URL should be cached after Test 2
assert "https://en.wikipedia.org" in _ROBOTS_CACHE
parser = _ROBOTS_CACHE["https://en.wikipedia.org"]
assert parser is not None

# Call again to ensure it hits the cache (no new network request)
assert is_crawl_allowed("https://en.wikipedia.org/wiki/DNS") is True
print("[OK] is_crawl_allowed: successfully cached robots.txt for domain")

# ── Test 4: Blocked URL ───────────────────────────────────────────────────────
# Wikipedia blocks crawling of its search endpoint
url_blocked = "https://en.wikipedia.org/w/index.php?search=foo"
assert is_crawl_allowed(url_blocked) is False
print("[OK] is_crawl_allowed: correctly blocks disallowed path (Wikipedia search)")

# ── Test 5: Missing robots.txt (404) defaults to allowed ──────────────────────
url_missing = "https://example.com/some/page"
# Standard example.com doesn't have a strict robots.txt blocking /some/page
# urllib will fail to fetch a meaningful blocklist and we return True
assert is_crawl_allowed(url_missing) is True
assert _ROBOTS_CACHE["https://example.com"] is None
print("[OK] is_crawl_allowed: defaults to allowed if robots.txt fails to load")

print("\n=== STEP 7 COMPLETE: robots.txt checker verified ===")
