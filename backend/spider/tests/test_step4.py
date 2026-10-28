# -*- coding: utf-8 -*-
"""
Test: STEP 4 - core/config.py
Run:  python test_step4.py
"""
import sys
sys.path.insert(0, ".")

from knowledge_spider.utils.logger import setup_logger
setup_logger("test_cfg")

from knowledge_spider.core.config import (
    load_config, get_config, reset_config,
    Config, CrawlerConfig, NLPConfig, ScoringConfig, ExportConfig,
)

# ── Test 1: load_config returns a Config instance ─────────────────────────────
reset_config()
cfg = load_config()
assert isinstance(cfg, Config)
print("[OK] load_config() returned a Config instance")

# ── Test 2: Crawler section values ───────────────────────────────────────────
assert cfg.crawler.max_depth == 3
assert cfg.crawler.max_sources == 200
assert cfg.crawler.crawl_delay_seconds == 2.0
assert cfg.crawler.max_urls_per_query == 5
assert cfg.crawler.respect_robots is True
assert cfg.crawler.trusted_only is False
print("[OK] CrawlerConfig: max_depth=3, max_sources=200, crawl_delay=2.0")

# ── Test 3: NLP section values ────────────────────────────────────────────────
assert cfg.nlp.min_content_words == 150
assert cfg.nlp.relevance_threshold == 0.45
assert cfg.nlp.max_topics_per_page == 8
assert cfg.nlp.summary_sentence_count == 5
print("[OK] NLPConfig: min_words=150, threshold=0.45, max_topics=8")

# ── Test 4: Scoring weights sum to 1.0 ───────────────────────────────────────
total = (cfg.scoring.domain_weight + cfg.scoring.content_weight
       + cfg.scoring.relevance_weight + cfg.scoring.freshness_weight)
assert abs(total - 1.0) < 0.01, "Weights must sum to 1.0, got " + str(total)
print("[OK] ScoringConfig: weights sum to " + str(round(total, 4)))

# ── Test 5: Domain scores ─────────────────────────────────────────────────────
assert cfg.domain_scores["wikipedia.org"] == 1.0
assert cfg.domain_scores["arxiv.org"] == 0.95
assert cfg.domain_scores["stackoverflow.com"] == 0.80
assert cfg.domain_scores["default"] == 0.40
print("[OK] domain_scores: wikipedia=1.0, arxiv=0.95, stackoverflow=0.80, default=0.40")

# ── Test 6: Trusted domains list ──────────────────────────────────────────────
assert len(cfg.trusted_domains) == 8
assert "wikipedia.org" in cfg.trusted_domains
assert "arxiv.org" in cfg.trusted_domains
assert "rfc-editor.org" in cfg.trusted_domains
print("[OK] trusted_domains: 8 entries including wikipedia, arxiv, rfc-editor")

# ── Test 7: get_domain_score helper ──────────────────────────────────────────
score_wiki = cfg.get_domain_score("wikipedia.org")
score_unknown = cfg.get_domain_score("some-random-blog.io")
assert score_wiki == 1.0
assert score_unknown == 0.40   # fallback to "default"
print("[OK] get_domain_score: wikipedia=1.0, unknown=0.40 (default)")

# ── Test 8: is_trusted_domain helper ─────────────────────────────────────────
assert cfg.is_trusted_domain("en.wikipedia.org") is True
assert cfg.is_trusted_domain("developer.mozilla.org") is True
assert cfg.is_trusted_domain("some-random-blog.io") is False
print("[OK] is_trusted_domain: wikipedia=True, moz=True, random=False")

# ── Test 9: get_config() returns cached singleton ─────────────────────────────
cfg2 = get_config()
assert cfg2 is cfg, "get_config() must return the same cached instance"
print("[OK] get_config() returns cached singleton (same object identity)")

# ── Test 10: reset_config() clears cache ─────────────────────────────────────
reset_config()
cfg3 = get_config()
assert cfg3 is not cfg, "After reset, a new Config object must be created"
print("[OK] reset_config() clears cache and triggers re-load")

# ── Test 11: to_json() produces valid JSON snapshot ──────────────────────────
import json
snapshot = cfg3.to_json()
parsed = json.loads(snapshot)
assert parsed["crawler"]["max_depth"] == 3
assert parsed["domain_scores"]["wikipedia.org"] == 1.0
assert len(parsed["trusted_domains"]) == 8
print("[OK] to_json() snapshot is valid JSON with correct values")

# ── Test 12: Export config ────────────────────────────────────────────────────
assert cfg3.export.output_dir == "./output"
assert cfg3.export.default_format == "json"
print("[OK] ExportConfig: output_dir='./output', format='json'")

print()
print("=== STEP 4 COMPLETE: Config loader fully verified (12/12 tests) ===")
