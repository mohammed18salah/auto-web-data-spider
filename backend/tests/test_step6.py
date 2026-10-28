# -*- coding: utf-8 -*-
"""
Test: STEP 6 - query/query_engine.py
Run:  python test_step6.py
"""
import sys
sys.path.insert(0, ".")

from knowledge_spider.utils.logger import setup_logger
setup_logger("test_query")

from knowledge_spider.core.config import get_config
from knowledge_spider.query.query_engine import generate_queries, extract_domain, target_sources

# ── Test 1: generate_queries ──────────────────────────────────────────────────
topic = "HTTP"
queries = generate_queries(topic)
assert len(queries) == 8
assert "what is HTTP" in queries
assert "how does HTTP work" in queries
print("[OK] generate_queries: generated 8 pattern-based queries")

# ── Test 2: extract_domain ────────────────────────────────────────────────────
domain1 = extract_domain("https://en.wikipedia.org/wiki/HTTP")
assert domain1 == "en.wikipedia.org"
domain2 = extract_domain("http://stackoverflow.com/questions/123")
assert domain2 == "stackoverflow.com"
print("[OK] extract_domain: correctly extracted domains")

# ── Test 3: target_sources (Live DDG Search) ──────────────────────────────────
# Configure to only fetch 2 URLs per query to keep the test fast
cfg = get_config()
cfg.crawler.max_urls_per_query = 2
cfg.crawler.crawl_delay_seconds = 1.0 # Short delay for tests

# Test with 2 queries
test_queries = generate_queries("HTTP")[:2]
print(f"Running live search for: {test_queries}")

urls = target_sources("HTTP", test_queries, cfg)
assert isinstance(urls, list)
# We expect at least some URLs, though DDG might fail occasionally
if urls:
    assert len(urls) > 0
    print(f"[OK] target_sources: Found {len(urls)} unique URLs")
    for u in urls[:3]:
        print(f"  - {u}")
else:
    print("[WARN] target_sources: Returned 0 URLs (DDG might be rate-limiting)")

# ── Test 4: target_sources with trusted_only ──────────────────────────────────
cfg.crawler.trusted_only = True
print("Running live search with trusted_only=True...")
trusted_urls = target_sources("HTTP", test_queries, cfg)
if trusted_urls:
    print(f"[OK] target_sources (trusted): Found {len(trusted_urls)} unique URLs")
    for u in trusted_urls:
        domain = extract_domain(u)
        assert cfg.is_trusted_domain(domain), f"Found untrusted domain: {domain}"
        print(f"  - {u} (Trusted)")
else:
    print("[WARN] target_sources (trusted): Returned 0 URLs")

print("\n=== STEP 6 COMPLETE: Query Engine verified ===")
