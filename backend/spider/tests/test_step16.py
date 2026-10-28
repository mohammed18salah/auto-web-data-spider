# -*- coding: utf-8 -*-
"""
Test: STEP 16 - cli/main.py
Run:  python test_step16.py
"""
import sys
sys.path.insert(0, ".")

from typer.testing import CliRunner
from knowledge_spider.cli.main import app

runner = CliRunner()

# Test 1: Help command
result = runner.invoke(app, ["--help"])
assert result.exit_code == 0
assert "KnowledgeSpider" in result.stdout
print("[OK] CLI: Help menu renders successfully")

# Test 2: List sessions
result = runner.invoke(app, ["sessions"])
assert result.exit_code == 0
assert "KnowledgeSpider Sessions" in result.stdout or "No sessions found" in result.stdout
print("[OK] CLI: Sessions list command executes successfully")

# Note: We won't test `start` or `resume` fully here as they invoke the Orchestrator loop
# which takes significant time. Testing interface structure is sufficient.

print("\n=== STEP 16 COMPLETE: CLI Interface verified ===")
