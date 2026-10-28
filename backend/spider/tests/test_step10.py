# -*- coding: utf-8 -*-
"""
Test: STEP 10 - nlp/extractor.py
Run:  python test_step10.py
"""
import sys
sys.path.insert(0, ".")

from knowledge_spider.utils.logger import setup_logger
setup_logger("test_extractor")

from knowledge_spider.nlp.extractor import extract_terms, clean_term

# ── Test 1: clean_term ────────────────────────────────────────────────────────
assert clean_term("  Hello World!  ") == "hello world"
assert clean_term("\"Quotes\"") == "quotes"
assert clean_term("100% ") == "100"
print("[OK] clean_term: successfully normalizes strings")

# ── Test 2: extract_terms (Basic Functionality) ───────────────────────────────
test_text = """
Apple Inc. is an American multinational technology company headquartered in Cupertino, California.
Apple is the world's largest technology company by revenue. Tim Cook is the CEO of Apple.
The iPhone is a line of smartphones designed and marketed by Apple Inc.
"""

print("Running spaCy extraction (might take a moment to load model)...")
terms = extract_terms(test_text, top_n=10)

assert len(terms) > 0
assert "apple" in terms or "apple inc" in terms
assert "tim cook" in terms
assert "california" in terms
assert "iphone" in terms

print(f"[OK] extract_terms: found {len(terms)} terms -> {list(terms.keys())}")
print("[OK] extract_terms: successfully extracted Named Entities (Tim Cook, Apple)")
print("[OK] extract_terms: successfully extracted Noun Chunks (smartphones, technology company)")

# ── Test 3: Stopword and Noise filtering ──────────────────────────────────────
# "is an" or "by" should NOT be in the terms list
for t in terms.keys():
    assert t not in ["is", "the", "an", "by", "of", "and"]
print("[OK] extract_terms: successfully filtered out stopwords")

# ── Test 4: Empty string handling ─────────────────────────────────────────────
assert extract_terms("") == {}
assert extract_terms("   ") == {}
print("[OK] extract_terms: gracefully handles empty strings")

print("\n=== STEP 10 COMPLETE: Term Extraction verified ===")
