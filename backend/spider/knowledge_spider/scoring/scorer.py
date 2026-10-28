"""
Module: scoring/scorer.py
Purpose: Quality Scoring Engine.
         Calculates a normalized score (0.0 to 1.0) for a source based on
         its text length, the density of NLP-extracted terms, its crawl depth,
         and the domain's configured authority score.
Author: KnowledgeSpider Engine
"""

from __future__ import annotations

import math

from knowledge_spider.core.config import Config, get_config
from knowledge_spider.utils.logger import logger


def calculate_quality_score(
    word_count: int,
    term_count: int,
    depth: int,
    domain: str,
    config: Config | None = None
) -> float:
    """
    Calculate a normalized quality score (0.0 to 1.0) for a web source.

    The score is a weighted sum of four normalized metrics:
      1. Length Score (L):   Normalised based on an ideal word count (e.g., 2000 words).
      2. Density Score (D):  Ratio of extracted terms to total words.
      3. Depth Score (R):    Decays as crawl depth increases.
      4. Domain Score (A):   Looked up directly from config.domain_scores.

    Args:
        word_count: Total words in the clean body text.
        term_count: Number of unique NLP terms extracted (from extractor.py).
        depth:      Crawl depth (0 for seed, 1 for links off seed, etc.).
        domain:     The URL's domain (e.g., "wikipedia.org").
        config:     Config instance. Defaults to global singleton.

    Returns:
        A float between 0.0 and 1.0.
    """
    cfg = config or get_config()
    weights = cfg.scoring

    if word_count == 0:
        return 0.0

    # 1. Length Score
    # We use a logistic-like function or simply cap at an "ideal" length.
    # An ideal article is ~2000 words. Above that, diminishing returns.
    ideal_length = 2000.0
    length_score = min(word_count / ideal_length, 1.0)

    # 2. Density Score
    # What % of the text is meaningful terms? 
    # E.g. 50 terms in 1000 words = 0.05. We cap this at a reasonable maximum (e.g., 0.15)
    # to prevent keyword stuffing from scoring a perfect 1.0.
    raw_density = term_count / word_count
    max_expected_density = 0.15
    density_score = min(raw_density / max_expected_density, 1.0)

    # 3. Relevance / Depth Score
    # Depth 0 (Seed) = 1.0
    # Depth 1 = 0.8
    # Depth 2 = 0.6
    # Depth 3 = 0.4...
    depth_decay_factor = 0.2
    depth_score = max(1.0 - (depth * depth_decay_factor), 0.1)

    # 4. Domain Authority
    domain_score = cfg.get_domain_score(domain)

    # Combine using the configured weights.
    # We blend length and density equally into the single 'content_weight'.
    # We'll treat 'freshness_weight' as a bonus for just being fetched now (1.0).
    blended_content_score = (length_score + density_score) / 2.0
    freshness_score = 1.0 # Since we don't parse last-modified yet

    final_score = (
        (blended_content_score * weights.content_weight) +
        (depth_score           * weights.relevance_weight) +
        (domain_score          * weights.domain_weight) +
        (freshness_score       * weights.freshness_weight)
    )

    # Ensure bounds
    final_score = max(0.0, min(final_score, 1.0))

    logger.debug(
        f"Score for {domain} (words={word_count}, depth={depth}): {final_score:.3f} "
        f"[C:{blended_content_score:.2f}, R:{depth_score:.2f}, A:{domain_score:.2f}]"
    )

    return final_score
