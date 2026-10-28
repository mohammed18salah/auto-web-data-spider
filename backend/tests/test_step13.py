# -*- coding: utf-8 -*-
"""
Test: STEP 13 - scoring/scorer.py
Run:  python test_step13.py
"""
import sys
sys.path.insert(0, ".")

from knowledge_spider.utils.logger import setup_logger
setup_logger("test_scorer")

from knowledge_spider.core.config import get_config
from knowledge_spider.scoring.scorer import calculate_quality_score

cfg = get_config()
# Ensure weights match expectations (they should sum to 1.0 from step 4)
w = cfg.scoring
print(f"Weights: C={w.content_weight}, F={w.freshness_weight}, R={w.relevance_weight}, A={w.domain_weight}")

# ── Test 1: Ideal Source ──────────────────────────────────────────────────────
# Seed topic (depth 0), perfect length (2000), great density (100/2000), highly trusted domain
score_ideal = calculate_quality_score(
    word_count=2000, 
    term_count=100, 
    depth=0, 
    domain="wikipedia.org", 
    config=cfg
)
assert 0.8 < score_ideal <= 1.0
print(f"[OK] Ideal Source Score: {score_ideal:.3f}")

# ── Test 2: Poor Source ───────────────────────────────────────────────────────
# Deep link (depth 3), very short (150 words), low density (1/150), unknown domain
score_poor = calculate_quality_score(
    word_count=150, 
    term_count=1, 
    depth=3, 
    domain="unknown-spam.com", 
    config=cfg
)
assert score_poor < 0.5
print(f"[OK] Poor Source Score:  {score_poor:.3f}")

# ── Test 3: Zero Words ────────────────────────────────────────────────────────
score_zero = calculate_quality_score(word_count=0, term_count=0, depth=0, domain="wikipedia.org", config=cfg)
assert score_zero == 0.0
print(f"[OK] Zero Words Score:   {score_zero:.3f}")

# ── Test 4: Depth decay verification ──────────────────────────────────────────
# Keeping everything else identical, depth 1 should score lower than depth 0
score_d0 = calculate_quality_score(word_count=1000, term_count=50, depth=0, domain="github.com", config=cfg)
score_d1 = calculate_quality_score(word_count=1000, term_count=50, depth=1, domain="github.com", config=cfg)
score_d3 = calculate_quality_score(word_count=1000, term_count=50, depth=3, domain="github.com", config=cfg)

assert score_d0 > score_d1 > score_d3
print(f"[OK] Depth Decay: depth=0 ({score_d0:.3f}) > depth=1 ({score_d1:.3f}) > depth=3 ({score_d3:.3f})")

print("\n=== STEP 13 COMPLETE: Quality Scorer verified ===")
