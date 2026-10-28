# -*- coding: utf-8 -*-
"""
Test: STEP 18 - export/exporter.py
Run:  python test_step18.py
"""
import sys
import json
import csv
from pathlib import Path
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
setup_logger("test_export")

from knowledge_spider.core.config import get_config
from knowledge_spider.storage.database import create_db_and_tables, create_topic, create_source
from knowledge_spider.storage.models import SessionModel, TopicModel, SourceModel
from knowledge_spider.export.exporter import DataExporter

# 1. Setup minimal DB
create_db_and_tables()
sess_id = "test-export-session"
db_module.create_session(SessionModel(id=sess_id, seed_topic="Testing", status="complete", config_snapshot="{}"))

# Nodes and sources
t1 = create_topic(TopicModel(session_id=sess_id, name="Testing", depth=0))
s1 = create_source(SourceModel(
    session_id=sess_id, 
    topic_id=t1.id, 
    url="http://example.com", 
    domain="example.com", 
    summary="A summary.", 
    quality_score=0.9,
    content_hash="hash1"
))

# 2. Run Exports
cfg = get_config()
cfg.export.output_dir = "./test_output_dir"
exporter = DataExporter(sess_id)

json_path = exporter.export_json()
csv_path = exporter.export_csv()

# 3. Verify JSON
assert json_path.exists()
with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)
    assert data["session"]["seed_topic"] == "Testing"
    assert len(data["topics"]) == 1
    assert data["topics"][0]["sources"][0]["url"] == "http://example.com"

print(f"[OK] Exporter: Successfully generated valid JSON file at {json_path}")

# 4. Verify CSV
assert csv_path.exists()
with open(csv_path, "r", encoding="utf-8") as f:
    reader = list(csv.reader(f))
    # Header + 1 row
    assert len(reader) == 2
    assert reader[0][0] == "topic_name"
    assert reader[1][0] == "Testing"
    assert reader[1][3] == "http://example.com"

print(f"[OK] Exporter: Successfully generated valid CSV file at {csv_path}")

# Cleanup
json_path.unlink()
csv_path.unlink()
Path(cfg.export.output_dir).rmdir()

print("\n=== STEP 18 COMPLETE: Export Engine verified ===")
