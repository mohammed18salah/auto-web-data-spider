# -*- coding: utf-8 -*-
"""
Test: STEP 12 - crawler/deduplicator.py
Run:  python test_step12.py
"""
import sys
sys.path.insert(0, ".")

# ── Redirect DB to in-memory for tests ───────────────────────────────────────
import knowledge_spider.storage.database as db_module
from sqlmodel import create_engine
db_module._engine = create_engine(
    "sqlite:///:memory:",
    echo=False,
    connect_args={"check_same_thread": False},
)

from knowledge_spider.utils.logger import setup_logger
setup_logger("test_dedup")

from knowledge_spider.storage.database import create_db_and_tables, create_source
from knowledge_spider.storage.models import SourceModel
from knowledge_spider.crawler.deduplicator import is_new_url, mark_url_visited, clear_deduplicator_cache

create_db_and_tables()
clear_deduplicator_cache()

# ── Test 1: New URL is recognized as new ──────────────────────────────────────
url1 = "https://example.com/page1"
assert is_new_url(url1) is True
print("[OK] is_new_url: returns True for a completely new URL")

# ── Test 2: mark_url_visited blocks subsequent checks (Memory) ────────────────
mark_url_visited(url1)
assert is_new_url(url1) is False
print("[OK] is_new_url: returns False after URL is marked visited in memory")

# ── Test 3: DB cross-reference blocks known URLs ──────────────────────────────
url2 = "https://example.com/page2"
assert is_new_url(url2) is True  # Should be new in memory

# Simulate storing it in the DB (like the orchestrator would do after processing)
dummy_source = SourceModel(
    session_id="dummy-session-uuid",
    topic_id=1,
    url=url2,
    domain="example.com",
    title="Test",
    content="Test content",
    summary="Test",
    content_hash="abc123hash",
    word_count=2
)
create_source(dummy_source)

# Now it should NOT be new, because the DB knows about it
assert is_new_url(url2) is False
print("[OK] is_new_url: returns False for a URL found in the SQLite database")

# ── Test 4: Empty/Invalid strings are rejected ────────────────────────────────
assert is_new_url("") is False
assert is_new_url("   ") is False
print("[OK] is_new_url: safely rejects empty or whitespace-only URLs")

# ── Test 5: Cache clearing works ──────────────────────────────────────────────
clear_deduplicator_cache()
# url2 is still in DB, so it should still be False
assert is_new_url(url2) is False
# url1 is not in DB, so clearing cache should make it True again
assert is_new_url(url1) is True
print("[OK] clear_deduplicator_cache: correctly resets memory state")

print("\n=== STEP 12 COMPLETE: URL Deduplicator verified ===")
