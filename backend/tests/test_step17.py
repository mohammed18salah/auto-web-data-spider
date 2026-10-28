# -*- coding: utf-8 -*-
"""
Test: STEP 17 - cli/shell.py
Run:  python test_step17.py
"""
import sys
import io
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
setup_logger("test_shell")

from knowledge_spider.storage.database import create_db_and_tables, create_topic, create_edge
from knowledge_spider.storage.models import TopicModel, TopicEdgeModel, SessionModel
from knowledge_spider.cli.shell import KnowledgeShell

# 1. Init DB and Session
create_db_and_tables()
sess_id = "test-shell-session"
db_module.create_session(SessionModel(id=sess_id, seed_topic="Python", status="complete", config_snapshot="{}"))

# 2. Mock Data
t1 = create_topic(TopicModel(session_id=sess_id, name="Python", depth=0))
t2 = create_topic(TopicModel(session_id=sess_id, name="Django", depth=1))
create_edge(TopicEdgeModel(session_id=sess_id, from_topic="Python", to_topic="Django", weight=0.9))

# 3. Test Shell Initialisation
shell = KnowledgeShell(sess_id)
assert shell.session_id == sess_id
assert shell.graph.number_of_nodes() == 2
print("[OK] Shell: Initialised successfully and loaded graph")

# 4. Test commands execution (capture stdout)
captured_output = io.StringIO()
original_stdout = sys.stdout
sys.stdout = captured_output

try:
    shell.do_summary("")
    shell.do_explore("Python")
    shell.do_sources("Python")
finally:
    sys.stdout = original_stdout

output = captured_output.getvalue()

assert "Nodes" in output
assert "Django" in output
assert "Edge Weight" in output
print("[OK] Shell: Interactive commands (summary, explore, sources) execute without crashing")

print("\n=== STEP 17 COMPLETE: Interactive Shell verified ===")
