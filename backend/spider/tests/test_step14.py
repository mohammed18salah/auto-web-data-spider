# -*- coding: utf-8 -*-
"""
Test: STEP 14 - crawler/orchestrator.py
Run:  python test_step14.py
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
setup_logger("test_orchestrator")

from knowledge_spider.storage.database import create_db_and_tables, get_topics_by_session
from knowledge_spider.core.session import create_session
from knowledge_spider.core.config import get_config
from knowledge_spider.crawler.orchestrator import CrawlerOrchestrator
from knowledge_spider.crawler.deduplicator import clear_deduplicator_cache
from knowledge_spider.crawler.robots import clear_robots_cache

create_db_and_tables()
clear_deduplicator_cache()
clear_robots_cache()

# Configure for a highly constrained, fast test run
cfg = get_config()
cfg.crawler.max_depth = 0               # Don't explore sub-topics
cfg.crawler.max_sources = 1             # Stop after exactly 1 successful page
cfg.crawler.max_urls_per_query = 1      # 1 DDG result per query
cfg.crawler.crawl_delay_seconds = 0.5   # Fast
cfg.nlp.min_content_words = 10          # Let short pages through
cfg.nlp.summary_sentences = 1           # Fast summary

# Mock DDG search to avoid rate limits failing the test
import knowledge_spider.crawler.orchestrator as orch
def mock_target_sources(topic, queries, cfg):
    return ["https://en.wikipedia.org/wiki/HTTP"]
orch.target_sources = mock_target_sources

# 1. Create a session
sess = create_session("HTTP Protocol", cfg)

# 2. Init orchestrator
orchestrator = CrawlerOrchestrator(sess.id, cfg)

# Verify seeding happened
topics = get_topics_by_session(sess.id)
assert len(topics) == 1
assert topics[0].name == "HTTP Protocol"
assert topics[0].depth == 0
assert topics[0].status == "queued"
print("[OK] Orchestrator initialization: successfully seeded root topic")

# 3. Run orchestrator
print("\nRunning Orchestrator (this will hit DDG and fetch 1 page)...")
orchestrator.run()

# 4. Verify results
from knowledge_spider.storage.database import get_session_stats
stats = get_session_stats(sess.id)

print(f"\nStats after run: {stats}")
assert stats["sources_total"] == 1
assert stats["topics_done"] == 1
assert stats["terms"] > 0
print("[OK] Orchestrator: successfully enforced max_sources=1 limit")
print("[OK] Orchestrator: successfully progressed topic from queued to done")
print(f"[OK] Orchestrator: extracted and persisted {stats['terms']} terms")

print("\n=== STEP 14 COMPLETE: Crawler Orchestrator verified ===")
