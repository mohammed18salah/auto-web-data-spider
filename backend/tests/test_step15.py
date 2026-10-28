# -*- coding: utf-8 -*-
"""
Test: STEP 15 - knowledge/graph.py
Run:  python test_step15.py
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
setup_logger("test_graph")

from knowledge_spider.storage.database import create_db_and_tables, create_topic, create_edge
from knowledge_spider.storage.models import TopicModel, TopicEdgeModel
from knowledge_spider.knowledge.graph import KnowledgeGraphManager

# 1. Init DB
create_db_and_tables()

# 2. Setup mock data
session_id = "test-graph-session"

# Nodes
t1 = create_topic(TopicModel(session_id=session_id, name="Artificial Intelligence", depth=0))
t2 = create_topic(TopicModel(session_id=session_id, name="Machine Learning", depth=1))
t3 = create_topic(TopicModel(session_id=session_id, name="Neural Networks", depth=2))
t4 = create_topic(TopicModel(session_id=session_id, name="Deep Learning", depth=3))
t5 = create_topic(TopicModel(session_id=session_id, name="Data Science", depth=1))

# Edges (AI -> ML, AI -> DS, ML -> NN, NN -> DL, ML -> DL)
e1 = create_edge(TopicEdgeModel(session_id=session_id, from_topic=t1.name, to_topic=t2.name, weight=0.9))
e2 = create_edge(TopicEdgeModel(session_id=session_id, from_topic=t1.name, to_topic=t5.name, weight=0.8))
e3 = create_edge(TopicEdgeModel(session_id=session_id, from_topic=t2.name, to_topic=t3.name, weight=0.85))
e4 = create_edge(TopicEdgeModel(session_id=session_id, from_topic=t3.name, to_topic=t4.name, weight=0.95))
e5 = create_edge(TopicEdgeModel(session_id=session_id, from_topic=t2.name, to_topic=t4.name, weight=0.7))

# 3. Test Graph Manager
manager = KnowledgeGraphManager(session_id)
graph = manager.build_graph()

assert graph.number_of_nodes() == 5
assert graph.number_of_edges() == 5
print("[OK] Graph Builder: Correctly imported nodes and edges from SQLite")

summary = manager.get_graph_summary()
print(f"\nGraph Summary:\n{summary}")

assert summary["total_nodes"] == 5
assert summary["total_edges"] == 5
assert len(summary["top_concepts"]) <= 3

# PageRank should identify "Deep Learning" or "Neural Networks" as highly central due to incoming edges
top_node = summary["top_concepts"][0]["topic"]
print(f"[OK] Graph Analysis: Most central topic is '{top_node}'")
assert top_node in ["Deep Learning", "Neural Networks", "Machine Learning"]

print("\n=== STEP 15 COMPLETE: Knowledge Graph verified ===")
