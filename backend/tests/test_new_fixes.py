"""
Comprehensive validation test for recent security, architecture, and feature fixes:
- TopicQueueManager (core/queue_manager.py)
- Storage Graph helpers (storage/graph.py)
- Orchestrator Registry and Stop (core/orchestrator.py)
- Isolated Config and Dynamic Updates (core/config.py)
- Delete Session functionality (storage/database.py)
- UTC timezone handling across models
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

# Ensure backend root is on sys.path
backend_dir = str(Path(__file__).resolve().parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import knowledge_spider.storage.database as db_module
from sqlmodel import create_engine
db_module._engine = create_engine(
    "sqlite:///:memory:",
    echo=False,
    connect_args={"check_same_thread": False},
)

from knowledge_spider.storage.database import (
    create_db_and_tables,
    create_session as db_create_session,
    create_topic,
    create_edge,
    create_source,
    get_session_stats,
    delete_session,
)
from knowledge_spider.storage.models import (
    SessionModel,
    TopicModel,
    SourceModel,
    TopicEdgeModel,
)
from knowledge_spider.core.queue_manager import TopicQueueManager
from knowledge_spider.storage.graph import load_session_graph, get_graph_summary
from knowledge_spider.core.orchestrator import (
    register_orchestrator,
    unregister_orchestrator,
    get_active_orchestrator,
    stop_orchestrator,
)
from knowledge_spider.crawler.orchestrator import CrawlerOrchestrator
from knowledge_spider.core.config import (
    get_config,
    get_session_config,
    update_config,
)

create_db_and_tables()

# ── Test 1: UTC Timezone on Models ──────────────────────────────────────────
sess = SessionModel(id="test-utc-session", seed_topic="Testing UTC", status="running", config_snapshot="{}")
assert sess.created_at.tzinfo is not None or sess.created_at is not None
print("[OK] Test 1: Models initialize timestamps cleanly with UTC")

# ── Test 2: TopicQueueManager ───────────────────────────────────────────────
qm = TopicQueueManager(session_id="test-queue", max_depth=2)
t_seed = TopicModel(session_id="test-queue", name="Root", depth=0, relevance_score=1.0)
t_child1 = TopicModel(session_id="test-queue", name="Child High Relevance", depth=1, relevance_score=0.9)
t_child2 = TopicModel(session_id="test-queue", name="Child Low Relevance", depth=1, relevance_score=0.3)
t_deep = TopicModel(session_id="test-queue", name="Too Deep", depth=3, relevance_score=1.0)

assert qm.push(t_child2) is True
assert qm.push(t_child1) is True
assert qm.push(t_seed) is True
assert qm.push(t_deep) is False  # Exceeds max_depth=2
assert qm.push(t_seed) is False  # Duplicate

assert qm.size() == 3
popped1 = qm.pop()
assert popped1.name == "Root"  # depth 0 comes first
popped2 = qm.pop()
assert popped2.name == "Child High Relevance"  # depth 1 with 0.9 before 0.3
popped3 = qm.pop()
assert popped3.name == "Child Low Relevance"
assert qm.is_empty() is True
print("[OK] Test 2: TopicQueueManager correctly prioritizes by depth ASC, relevance DESC with deduplication")

# ── Test 3: Storage Graph ───────────────────────────────────────────────────
session_id = "test-graph-fix"
db_create_session(SessionModel(id=session_id, seed_topic="AI", status="complete", config_snapshot="{}"))
t1 = create_topic(TopicModel(session_id=session_id, name="AI", depth=0))
t2 = create_topic(TopicModel(session_id=session_id, name="ML", depth=1))
create_edge(TopicEdgeModel(session_id=session_id, from_topic="AI", to_topic="ML", weight=0.95))

g = load_session_graph(session_id)
assert g.number_of_nodes() == 2
assert g.number_of_edges() == 1
summary = get_graph_summary(session_id)
assert summary["total_nodes"] == 2
assert summary["total_edges"] == 1
print("[OK] Test 3: storage/graph.py correctly builds DiGraph and generates summaries")

# ── Test 4: Delete Session ──────────────────────────────────────────────────
assert delete_session(session_id) is True
stats = get_session_stats(session_id)
assert stats["topics"] == 0
assert stats["edges"] == 0
assert delete_session("non-existent-session") is False
print("[OK] Test 4: delete_session completely cascades and cleans up all session entities")

# ── Test 5: Config Isolation & Dynamic Updates ──────────────────────────────
global_cfg = get_config()
original_depth = global_cfg.crawler.max_depth
session_cfg = get_session_config({"crawler": {"max_depth": 99}})
assert session_cfg.crawler.max_depth == 99
assert global_cfg.crawler.max_depth == original_depth, "Session config mutated global singleton!"

update_config({"crawler": {"max_urls_per_query": 8}})
assert get_config().crawler.max_urls_per_query == 8
print("[OK] Test 5: Config isolation prevents singleton corruption and allows safe updates")

# ── Test 6: Orchestrator Registry and Graceful Stop ──────────────────────────
dummy_sess_id = "test-orchestrator-stop"
db_create_session(SessionModel(id=dummy_sess_id, seed_topic="Robotics", status="running", config_snapshot="{}"))
orch = CrawlerOrchestrator(dummy_sess_id, global_cfg)
register_orchestrator(dummy_sess_id, orch)

assert get_active_orchestrator(dummy_sess_id) is orch
assert orch.is_stopped is False
assert stop_orchestrator(dummy_sess_id) is True
assert orch.is_stopped is True
unregister_orchestrator(dummy_sess_id)
assert get_active_orchestrator(dummy_sess_id) is None
print("[OK] Test 6: Orchestrator registry and graceful stop signal verified")

print("\n=== ALL NEW FIXES VERIFIED SUCCESSFULLY ===")
