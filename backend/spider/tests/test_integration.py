# -*- coding: utf-8 -*-
"""
Test: STEP 19 - Full End-to-End Integration Test
Purpose: Validates the complete KnowledgeSpider pipeline in sequence:
         create session -> orchestrate crawl -> build graph -> export
Run:     python test_integration.py
"""
import sys
import json
import shutil
from pathlib import Path
sys.path.insert(0, ".")

# ── Step 1: Redirect all DB to a fresh file-based SQLite for this test ────────
from pathlib import Path
TEST_DB = Path("./integration_test.db")
if TEST_DB.exists():
    TEST_DB.unlink()

import knowledge_spider.storage.database as db_module
from sqlmodel import create_engine
db_module._engine = create_engine(
    f"sqlite:///{TEST_DB.resolve()}",
    echo=False,
    connect_args={"check_same_thread": False},
)

from knowledge_spider.utils.logger import setup_logger
setup_logger("integration_test")

from knowledge_spider.core.config import get_config
from knowledge_spider.core.session import create_session
from knowledge_spider.storage.database import create_db_and_tables, get_session_stats
from knowledge_spider.crawler.deduplicator import clear_deduplicator_cache
from knowledge_spider.crawler.robots import clear_robots_cache
from knowledge_spider.crawler.orchestrator import CrawlerOrchestrator
from knowledge_spider.knowledge.graph import KnowledgeGraphManager
from knowledge_spider.export.exporter import DataExporter

# ── Step 2: Configure for minimal, deterministic test run ─────────────────────
create_db_and_tables()
clear_deduplicator_cache()
clear_robots_cache()

cfg = get_config()
cfg.crawler.max_depth      = 1     # Allow 1 level of sub-topics to be discovered
cfg.crawler.max_sources    = 2     # Stop after 2 sources total
cfg.crawler.max_urls_per_query = 1 # 1 DDG result per query
cfg.crawler.crawl_delay_seconds = 0.3
cfg.nlp.min_content_words  = 50
cfg.nlp.max_topics_per_page = 3    # Cap branches to 3 sub-topics for speed
cfg.export.output_dir = "./integration_output"

# ── Step 3: Mock DDG to point to known good Wikipedia pages ──────────────────
import knowledge_spider.crawler.orchestrator as orch_module
MOCK_URLS = {
    "DNS": ["https://en.wikipedia.org/wiki/Domain_Name_System"],
    "default": ["https://en.wikipedia.org/wiki/Internet_protocol_suite"]
}
def mock_target_sources(topic, queries, cfg):
    return MOCK_URLS.get(topic, MOCK_URLS["default"])

orch_module.target_sources = mock_target_sources

print("=" * 60)
print("  KnowledgeSpider - Full Integration Test")
print("=" * 60)

# ── Step 4: Create Session ────────────────────────────────────────────────────
session = create_session("DNS", cfg)
print(f"\n[1/5] Session created: {session.id[:8]}... | Topic: {session.seed_topic}")

# ── Step 5: Run Orchestrator ──────────────────────────────────────────────────
print("[2/5] Starting Orchestrator (fetching Wikipedia pages)...")
orchestrator = CrawlerOrchestrator(session.id, cfg)
orchestrator.run()

stats = get_session_stats(session.id)
print(f"      Sources collected: {stats['sources_total']}")
print(f"      Topics discovered: {stats['topics']}")
print(f"      Terms extracted:   {stats['terms']}")
print(f"      Avg quality score: {stats['avg_quality']:.3f}")

assert stats["sources_total"] >= 1, "Expected at least 1 source to be persisted"
assert stats["topics"] >= 1, "Expected at least 1 topic to exist"
assert stats["terms"] > 0, "Expected NLP terms to be extracted"
print("      [OK] Orchestrator assertions passed")

# ── Step 6: Build Knowledge Graph ─────────────────────────────────────────────
print("\n[3/5] Building Knowledge Graph...")
manager = KnowledgeGraphManager(session.id)
summary = manager.get_graph_summary()
print(f"      Nodes: {summary['total_nodes']}")
print(f"      Edges: {summary['total_edges']}")
if summary["top_concepts"]:
    print(f"      Top concept: {summary['top_concepts'][0]['topic']} (PageRank {summary['top_concepts'][0]['pagerank']:.4f})")

assert summary["total_nodes"] >= 1, "Graph must have at least 1 node"
print("      [OK] Knowledge Graph assertions passed")

# ── Step 7: JSON Export ───────────────────────────────────────────────────────
print("\n[4/5] Exporting to JSON...")
exporter = DataExporter(session.id)
json_path = exporter.export_json()
assert json_path.exists()

with open(json_path, "r", encoding="utf-8") as f:
    payload = json.load(f)

assert payload["session"]["seed_topic"] == "DNS"
assert payload["topics"][0]["sources"][0]["url"] is not None
print(f"      [OK] JSON export verified: {json_path}")

# ── Step 8: CSV Export ────────────────────────────────────────────────────────
print("\n[5/5] Exporting to CSV...")
csv_path = exporter.export_csv()
assert csv_path.exists()
with open(csv_path, "r", encoding="utf-8") as f:
    lines = f.readlines()
# At least header + 1 row
assert len(lines) >= 2, "Expected header + at least 1 row in CSV"
print(f"      [OK] CSV export verified: {csv_path} ({len(lines)-1} rows)")

# ── Cleanup ───────────────────────────────────────────────────────────────────
shutil.rmtree("./integration_output", ignore_errors=True)
# Dispose engine to release the Windows file lock before deletion
if db_module._engine is not None:
    db_module._engine.dispose()
    db_module._engine = None
if TEST_DB.exists():
    try:
        TEST_DB.unlink()
    except PermissionError:
        pass  # Windows may still hold the file; leave it for OS cleanup

print("\n" + "=" * 60)
print("  STEP 19 COMPLETE: All integration assertions passed!")
print("=" * 60)
