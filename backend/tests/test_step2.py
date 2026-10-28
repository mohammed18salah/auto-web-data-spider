# -*- coding: utf-8 -*-
"""
Test: STEP 2 - storage/models.py
Run:  python test_step2.py
"""
import sys
sys.path.insert(0, ".")

from datetime import datetime
from knowledge_spider.storage.models import (
    SessionModel, TopicModel, SourceModel, TopicEdgeModel, TermModel,
    Session, Topic, Source, TopicEdge, Term,
)

# ── Test 1: Alias exports match the model classes ────────────────────────────
assert Session is SessionModel
assert Topic   is TopicModel
assert Source  is SourceModel
assert TopicEdge is TopicEdgeModel
assert Term    is TermModel
print("[OK] models: alias exports (Session, Topic, Source, TopicEdge, Term) correct")

# ── Test 2: SessionModel instantiation ───────────────────────────────────────
import uuid, json
sid = str(uuid.uuid4())
session = SessionModel(
    id=sid,
    seed_topic="DNS",
    status="running",
    config_snapshot=json.dumps({"max_depth": 3}),
)
assert session.id == sid
assert session.seed_topic == "DNS"
assert session.status == "running"
assert isinstance(session.created_at, datetime)
assert json.loads(session.config_snapshot)["max_depth"] == 3
print("[OK] SessionModel: id=" + session.id[:8] + "..., seed_topic=" + session.seed_topic)

# ── Test 3: TopicModel instantiation ─────────────────────────────────────────
topic = TopicModel(
    session_id=sid,
    name="DNS over HTTPS",
    depth=1,
    relevance_score=0.87,
    status="queued",
    is_seed=False,
)
assert topic.name == "DNS over HTTPS"
assert topic.depth == 1
assert topic.relevance_score == 0.87
assert topic.status == "queued"
assert topic.is_seed is False
assert topic.id is None  # not yet persisted
print("[OK] TopicModel: name=" + topic.name + ", depth=" + str(topic.depth))

# ── Test 4: SourceModel instantiation ────────────────────────────────────────
source = SourceModel(
    session_id=sid,
    topic_id=1,
    url="https://en.wikipedia.org/wiki/Domain_Name_System",
    domain="wikipedia.org",
    title="Domain Name System - Wikipedia",
    summary="DNS maps human-readable hostnames to IP addresses.",
    quality_score=0.92,
    depth_level=0,
    content_hash="a" * 64,
    word_count=3200,
)
assert source.domain == "wikipedia.org"
assert source.quality_score == 0.92
assert len(source.content_hash) == 64
assert source.word_count == 3200
print("[OK] SourceModel: url=" + source.url[:40] + "..., quality=" + str(source.quality_score))

# ── Test 5: TopicEdgeModel instantiation ─────────────────────────────────────
edge = TopicEdgeModel(
    session_id=sid,
    from_topic="DNS",
    to_topic="DNS over HTTPS",
    weight=0.75,
)
assert edge.from_topic == "DNS"
assert edge.to_topic == "DNS over HTTPS"
assert edge.weight == 0.75
print("[OK] TopicEdgeModel: " + edge.from_topic + " -> " + edge.to_topic + " (w=" + str(edge.weight) + ")")

# ── Test 6: TermModel instantiation ──────────────────────────────────────────
term = TermModel(
    session_id=sid,
    topic_id=1,
    term="name resolution",
    tfidf_score=0.63,
    frequency=14,
)
assert term.term == "name resolution"
assert term.tfidf_score == 0.63
assert term.frequency == 14
print("[OK] TermModel: term='" + term.term + "', tfidf=" + str(term.tfidf_score))

# ── Test 7: Table names are correct ──────────────────────────────────────────
assert SessionModel.__tablename__ == "sessions"
assert TopicModel.__tablename__ == "topics"
assert SourceModel.__tablename__ == "sources"
assert TopicEdgeModel.__tablename__ == "topic_edges"
assert TermModel.__tablename__ == "terms"
print("[OK] Table names: sessions, topics, sources, topic_edges, terms")

# ── Test 8: Required fields have correct Python types ────────────────────────
assert isinstance(session.id, str)
assert isinstance(topic.relevance_score, float)
assert isinstance(source.word_count, int)
assert isinstance(edge.weight, float)
assert isinstance(term.frequency, int)
print("[OK] Field types: str, float, int all correct")

print()
print("=== STEP 2 COMPLETE: All 5 models verified (no DB needed) ===")
