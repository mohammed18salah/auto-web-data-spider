# -*- coding: utf-8 -*-
"""
Test: STEP 5 - core/session.py
Run:  python test_step5.py
Uses an in-memory SQLite DB so no leftover files.
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
setup_logger("test_session")

from knowledge_spider.core.session import (
    create_session, load_session, save_session_state,
    mark_session_complete, pause_session, list_sessions,
    get_session_summary, assert_resumable,
    STATUS_RUNNING, STATUS_PAUSED, STATUS_COMPLETE,
)
from knowledge_spider.storage.database import create_db_and_tables
create_db_and_tables()

# ── Test 1: create_session ────────────────────────────────────────────────────
sess = create_session("DNS")
assert sess.id is not None
assert len(sess.id) == 36               # UUID format
assert sess.seed_topic == "DNS"
assert sess.status == STATUS_RUNNING
assert sess.config_snapshot != "{}"     # JSON was written
print("[OK] create_session: id=" + sess.id[:8] + "... topic=DNS status=running")

# ── Test 2: load_session roundtrip ───────────────────────────────────────────
reloaded = load_session(sess.id)
assert reloaded.id == sess.id
assert reloaded.seed_topic == "DNS"
assert reloaded.status == STATUS_RUNNING
print("[OK] load_session: reloaded id=" + reloaded.id[:8] + "... correctly")

# ── Test 3: load_session with bad ID raises ValueError ────────────────────────
try:
    load_session("00000000-0000-0000-0000-000000000000")
    assert False, "Should have raised ValueError"
except ValueError as e:
    assert "not found" in str(e)
print("[OK] load_session: raises ValueError for unknown session_id")

# ── Test 4: save_session_state (generic) ─────────────────────────────────────
save_session_state(sess.id, STATUS_PAUSED)
chk = load_session(sess.id)
assert chk.status == STATUS_PAUSED
print("[OK] save_session_state: status updated to paused")

# ── Test 5: mark_session_complete ────────────────────────────────────────────
mark_session_complete(sess.id)
chk2 = load_session(sess.id)
assert chk2.status == STATUS_COMPLETE
print("[OK] mark_session_complete: status=complete")

# ── Test 6: pause_session ────────────────────────────────────────────────────
sess2 = create_session("HTTP")
pause_session(sess2.id)
chk3 = load_session(sess2.id)
assert chk3.status == STATUS_PAUSED
print("[OK] pause_session: HTTP session status=paused")

# ── Test 7: list_sessions returns both ───────────────────────────────────────
all_sessions = list_sessions()
assert len(all_sessions) >= 2
ids = [s.id for s in all_sessions]
assert sess.id  in ids
assert sess2.id in ids
print("[OK] list_sessions: found " + str(len(all_sessions)) + " sessions")

# ── Test 8: get_session_summary dict structure ───────────────────────────────
# Need to create a topic + source first to get non-zero stats
from knowledge_spider.storage.database import create_topic
from knowledge_spider.storage.models import TopicModel

t = create_topic(TopicModel(
    session_id=sess.id, name="DNS", depth=0,
    relevance_score=1.0, status="done", is_seed=True,
))
summary = get_session_summary(sess.id)
assert summary["id"] == sess.id
assert summary["seed_topic"] == "DNS"
assert summary["status"] == STATUS_COMPLETE
assert "created_at" in summary
assert "stats" in summary
assert summary["stats"]["topics"] >= 1
print("[OK] get_session_summary: keys present, stats.topics=" + str(summary["stats"]["topics"]))

# ── Test 9: assert_resumable allows paused sessions ──────────────────────────
resumable = assert_resumable(sess2.id)
assert resumable.id == sess2.id
print("[OK] assert_resumable: paused session passes guard")

# ── Test 10: assert_resumable blocks completed sessions ──────────────────────
try:
    assert_resumable(sess.id)   # status=complete
    assert False, "Should have raised ValueError"
except ValueError as e:
    assert "complete" in str(e)
print("[OK] assert_resumable: raises ValueError for complete session")

# ── Test 11: config_snapshot is valid JSON with expected keys ─────────────────
import json
snap = json.loads(sess.config_snapshot)
assert "crawler" in snap
assert snap["crawler"]["max_depth"] == 3
assert snap["domain_scores"]["wikipedia.org"] == 1.0
print("[OK] config_snapshot JSON: max_depth=3, wikipedia=1.0")

# ── Test 12: seed_topic is stripped of whitespace ─────────────────────────────
sess3 = create_session("  Machine Learning  ")
assert sess3.seed_topic == "Machine Learning"
print("[OK] create_session: seed_topic stripped of whitespace")

print()
print("=== STEP 5 COMPLETE: Session manager fully verified (12/12 tests) ===")
