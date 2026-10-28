# -*- coding: utf-8 -*-
"""
Test: STEP 3 - storage/database.py
Run:  python test_step3.py
Uses an in-memory :memory: SQLite DB so no files are left behind.
"""
import sys
sys.path.insert(0, ".")

import uuid, json
from datetime import datetime
from pathlib import Path

# ── Redirect engine to an in-memory DB for tests ─────────────────────────────
import knowledge_spider.storage.database as db_module
from sqlmodel import create_engine
db_module._engine = create_engine(
    "sqlite:///:memory:",
    echo=False,
    connect_args={"check_same_thread": False},
)

from knowledge_spider.storage.database import (
    create_db_and_tables,
    create_session, get_session_by_id, update_session_status, list_sessions,
    create_topic, get_topic_by_name, update_topic_status, get_topics_by_session,
    create_source, source_exists, get_sources_by_topic,
    create_edge, get_edges_by_session,
    bulk_insert_terms, get_terms_by_topic,
    get_session_stats,
)
from knowledge_spider.storage.models import (
    SessionModel, TopicModel, SourceModel, TopicEdgeModel, TermModel,
)

# ── Setup ─────────────────────────────────────────────────────────────────────
create_db_and_tables()
print("[OK] database: tables created (in-memory SQLite)")

# ── Test 1: Session CRUD ──────────────────────────────────────────────────────
sid = str(uuid.uuid4())
sess = create_session(SessionModel(
    id=sid,
    seed_topic="DNS",
    status="running",
    config_snapshot=json.dumps({"max_depth": 3}),
))
assert sess.id == sid
assert sess.seed_topic == "DNS"

fetched = get_session_by_id(sid)
assert fetched is not None
assert fetched.seed_topic == "DNS"

ok = update_session_status(sid, "paused")
assert ok is True
refreshed = get_session_by_id(sid)
assert refreshed.status == "paused"

sessions = list_sessions()
assert len(sessions) >= 1
print("[OK] Session CRUD: create, get_by_id, update_status, list_sessions")

# ── Test 2: Topic CRUD ────────────────────────────────────────────────────────
t1 = create_topic(TopicModel(
    session_id=sid, name="DNS", depth=0,
    relevance_score=1.0, status="done", is_seed=True,
))
t2 = create_topic(TopicModel(
    session_id=sid, name="DNS over HTTPS", depth=1,
    relevance_score=0.85, status="queued", is_seed=False,
))
assert t1.id is not None
assert t2.id is not None

found = get_topic_by_name(sid, "DNS over HTTPS")
assert found is not None
assert found.name == "DNS over HTTPS"

ok = update_topic_status(t2.id, "processing")
assert ok is True

topics = get_topics_by_session(sid)
assert len(topics) == 2
print("[OK] Topic CRUD: create, get_by_name, update_status, get_by_session")

# ── Test 3: Source CRUD + dedup ───────────────────────────────────────────────
hash1 = "a" * 64
hash2 = "b" * 64

s1 = create_source(SourceModel(
    session_id=sid, topic_id=t1.id,
    url="https://en.wikipedia.org/wiki/DNS",
    domain="wikipedia.org", title="DNS - Wikipedia",
    summary="DNS maps hostnames to IPs.",
    quality_score=0.92, depth_level=0,
    content_hash=hash1, word_count=3200,
))
assert s1 is not None

# Duplicate insert — must return None
s1_dup = create_source(SourceModel(
    session_id=sid, topic_id=t1.id,
    url="https://en.wikipedia.org/wiki/DNS_v2",
    domain="wikipedia.org", title="DNS duplicate",
    summary="same content", quality_score=0.9,
    depth_level=0, content_hash=hash1, word_count=100,
))
assert s1_dup is None, "Duplicate source should return None"

# source_exists checks
assert source_exists(hash1) is True
assert source_exists("c" * 64) is False

s2 = create_source(SourceModel(
    session_id=sid, topic_id=t1.id,
    url="https://arxiv.org/abs/1234",
    domain="arxiv.org", title="DNS paper",
    summary="Arxiv DNS paper.", quality_score=0.88,
    depth_level=1, content_hash=hash2, word_count=5000,
))
assert s2 is not None

src_list = get_sources_by_topic(t1.id)
assert len(src_list) == 2
assert src_list[0].quality_score >= src_list[1].quality_score  # ordered desc
print("[OK] Source CRUD: create, dedup, source_exists, get_by_topic")

# ── Test 4: TopicEdge CRUD + dedup ────────────────────────────────────────────
e1 = create_edge(TopicEdgeModel(session_id=sid, from_topic="DNS", to_topic="DNS over HTTPS", weight=0.75))
assert e1 is not None

e1_dup = create_edge(TopicEdgeModel(session_id=sid, from_topic="DNS", to_topic="DNS over HTTPS", weight=0.5))
assert e1_dup is None, "Duplicate edge should return None"

e2 = create_edge(TopicEdgeModel(session_id=sid, from_topic="DNS", to_topic="DNSSEC", weight=0.6))
assert e2 is not None

edges = get_edges_by_session(sid)
assert len(edges) == 2
print("[OK] TopicEdge CRUD: create, dedup, get_by_session")

# ── Test 5: Term CRUD ─────────────────────────────────────────────────────────
terms_data = [
    TermModel(session_id=sid, topic_id=t1.id, term="name server", tfidf_score=0.72, frequency=18),
    TermModel(session_id=sid, topic_id=t1.id, term="ip address",  tfidf_score=0.65, frequency=23),
    TermModel(session_id=sid, topic_id=t1.id, term="recursive",   tfidf_score=0.58, frequency=11),
]
inserted = bulk_insert_terms(terms_data)
assert inserted == 3

term_list = get_terms_by_topic(t1.id)
assert len(term_list) == 3
assert term_list[0].tfidf_score >= term_list[1].tfidf_score  # ordered desc
print("[OK] Term CRUD: bulk_insert_terms, get_terms_by_topic")

# ── Test 6: Stats helper ──────────────────────────────────────────────────────
stats = get_session_stats(sid)
assert stats["topics"] == 2
assert stats["sources_total"] == 2
assert stats["edges"] == 2
assert stats["terms"] == 3
assert stats["topics_done"] == 1
assert stats["avg_quality"] > 0
print("[OK] Stats: topics=" + str(stats["topics"]) +
      ", sources=" + str(stats["sources_total"]) +
      ", edges=" + str(stats["edges"]) +
      ", avg_quality=" + str(stats["avg_quality"]))

print()
print("=== STEP 3 COMPLETE: Database layer fully verified ===")
