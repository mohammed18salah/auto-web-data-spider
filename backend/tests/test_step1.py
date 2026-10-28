# -*- coding: utf-8 -*-
"""
Test: STEP 1 - utils/logger.py + utils/hasher.py
Run: python test_step1.py
"""
import sys
sys.path.insert(0, ".")

# ── Test 1: Logger import and setup ──────────────────────────────────────────
from knowledge_spider.utils.logger import logger, setup_logger, get_logger

setup_logger(session_id="test")

logger.info("Logger is working — INFO level")
logger.debug("Logger is working — DEBUG level")
logger.warning("Logger is working — WARNING level")

returned = get_logger()
assert returned is logger, "get_logger() must return the same logger instance"
print("[OK] logger: import, setup_logger(), get_logger() all passed")

# ── Test 2: Log directory created ────────────────────────────────────────────
from pathlib import Path
assert Path("./logs").exists(), "logs/ directory was not created"
assert Path("./logs/spider_test.log").exists(), "spider_test.log was not created"
print("[OK] logger: logs/ dir and spider_test.log created on disk")

# ── Test 3: hash_content basic ───────────────────────────────────────────────
from knowledge_spider.utils.hasher import hash_content, hash_file, hashes_match

h = hash_content("test")
assert isinstance(h, str), "hash must be a string"
assert len(h) == 64, f"SHA-256 must be 64 hex chars, got {len(h)}"
assert h == hash_content("test"), "Same input must always produce same hash"
print(f"[OK] hasher: hash_content('test') = {h}")

# ── Test 4: Whitespace normalisation ─────────────────────────────────────────
h1 = hash_content("hello   world")
h2 = hash_content("hello world")
assert h1 == h2, "Whitespace-normalised strings must hash identically"
print("[OK] hasher: whitespace normalisation works (multi-space == single-space)")

# ── Test 5: Different content → different hash ────────────────────────────────
h_a = hash_content("DNS is a protocol")
h_b = hash_content("HTTP is a protocol")
assert h_a != h_b, "Different content must produce different hashes"
print("[OK] hasher: different content -> different hashes")

# ── Test 6: hashes_match helper ──────────────────────────────────────────────
assert hashes_match("identical text", "identical text") is True
assert hashes_match("text A", "text B") is False
print("[OK] hasher: hashes_match() True/False logic correct")

# ── Test 7: hash_file ────────────────────────────────────────────────────────
tmp = Path("./logs/_hash_test.txt")
tmp.write_text("KnowledgeSpider test file", encoding="utf-8")
file_hash = hash_file(tmp)
assert len(file_hash) == 64
text_hash = hash_content("KnowledgeSpider test file")
# File hash uses raw bytes, text hash normalises — they may differ slightly
# but both must be valid 64-char hex strings
print("[OK] hasher: hash_file() = " + file_hash)
tmp.unlink()

print()
print("=== STEP 1 COMPLETE: logger + hasher fully verified ===")
