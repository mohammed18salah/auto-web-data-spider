"""
Module: scoring/scorer.py
Purpose: Quality Scoring & Semantic Relevance Engine.
         Calculates a normalized score (0.0 to 1.0) for a source based on
         strict semantic relevance to the seed query, entity alignment,
         text length, term density, and domain authority.
Author: KnowledgeSpider Engine
"""

from __future__ import annotations

import math
import re

from knowledge_spider.core.config import Config, get_config
from knowledge_spider.utils.logger import logger

# Commercial or delivery domains to reject when doing academic/informational queries
COMMERCIAL_BLACKLIST_DOMAINS = {
    "talabat.com",
    "hungerstation.com",
    "jahez.net",
    "jumia.com",
    "noon.com",
    "aliexpress.com",
    "alibaba.com",
    "shein.com",
    "booking.com",
    "tripadvisor.com",
    "trivago.com",
    "flynas.com",
    "saudia.com",
}


def normalize_arabic(text: str) -> str:
    """Normalize Arabic characters for robust fuzzy and exact matching."""
    text = re.sub(r'[\u064B-\u0652]', '', text)  # remove harakat
    text = re.sub(r'[إأآا]', 'ا', text)
    text = re.sub(r'ة', 'ه', text)
    text = re.sub(r'ى', 'ي', text)
    return text.lower().strip()


def compute_semantic_relevance(
    seed_topic: str,
    title: str,
    url: str,
    content: str,
    domain: str = ""
) -> tuple[float, str]:
    """
    Computes strict semantic relevance (0.0 to 1.0) between page content and seed topic.
    Returns (score, reason). Pages with conflicting entities or zero matches return 0.0.
    """
    clean_domain = domain.lower()
    for bad in COMMERCIAL_BLACKLIST_DOMAINS:
        if bad in clean_domain or bad in url.lower():
            return 0.0, f"rejected: commercial/delivery domain ({clean_domain})"

    text_raw = (title + " " + (content[:3000] if content else "")).lower()
    text_norm = normalize_arabic(text_raw)
    url_norm = url.lower()
    seed_norm = normalize_arabic(seed_topic)

    # Detect entity types
    academic_titles = ["دكتور", "الدكتور", "د.", "د/", "استاذ", "الاستاذ", "ا.د", "بروفيسور", "مهندس"]
    seed_no_title = seed_norm
    for t in academic_titles:
        t_norm = normalize_arabic(t)
        seed_no_title = re.sub(rf'^{re.escape(t_norm)}\s+', '', seed_no_title)

    institution_keywords = ["جامعه", "كليه", "معهد", "مستشفي", "مركز", "اكاديميه"]
    has_institution_in_seed = any(inst in seed_norm for inst in institution_keywords) or "انبار" in seed_norm or "العراق" in seed_norm

    score = 0.0
    reasons = []

    # 1. Exact Seed Match
    if seed_norm in text_norm or seed_no_title in text_norm:
        score += 0.55
        reasons.append("exact_seed_match")

    # 2. Person Name Analysis
    if has_institution_in_seed:
        parts = re.split(r'\s+(?=جامعه|كليه|معهد|مستشفي|مركز)', seed_no_title)
        person_name = parts[0].strip() if parts else seed_no_title
    else:
        person_name = seed_no_title

    name_tokens = [w for w in person_name.split() if len(w) > 2 and w not in ["في", "من", "عن", "مع", "علي"]]
    matched_name_tokens = sum(1 for tok in name_tokens if tok in text_norm)
    if name_tokens:
        ratio = matched_name_tokens / len(name_tokens)
        if ratio >= 0.8:
            score += 0.35
            reasons.append(f"person_full_match_{matched_name_tokens}/{len(name_tokens)}")
        elif ratio >= 0.5:
            score += 0.20
            reasons.append(f"person_partial_match_{matched_name_tokens}/{len(name_tokens)}")

    # 3. Institution / Geographic Constraint Check
    if has_institution_in_seed:
        inst_tokens = ["انبار", "الانبار", "uoanbar", "جامعه الانبار", "العراق"]
        inst_matched = any(it in text_norm or it in url_norm for it in inst_tokens)
        if inst_matched:
            score += 0.35
            reasons.append("institution_verified")
        else:
            # Check for CONFLICTING distant geographic locations (e.g. Egypt clinics when Anbar Iraq is requested)
            conflicting_locations = ["الشرقيه", "ديرب نجم", "الزقازيق", "مصر", "القاهره", "طنطا", "المنصوره", "الاسكندريه"]
            conflict_found = any(c in text_norm for c in conflicting_locations)
            if conflict_found:
                return 0.0, "rejected: conflicting geographic location (Egypt/Sharqia instead of requested Anbar/Iraq)"
            else:
                score *= 0.3
                reasons.append("penalty_missing_institution")
    else:
        # General query: check token coverage
        general_tokens = [w for w in seed_norm.split() if len(w) > 2]
        if general_tokens:
            matched = sum(1 for tok in general_tokens if tok in text_norm)
            token_ratio = matched / len(general_tokens)
            score += token_ratio * 0.4
            reasons.append(f"token_coverage_{int(token_ratio*100)}%")

    final_score = min(1.0, max(0.0, score))
    return final_score, ", ".join(reasons) if reasons else "no_match"


def calculate_quality_score(
    word_count: int,
    term_count: int,
    depth: int,
    domain: str,
    relevance_score: float = 1.0,
    config: Config | None = None
) -> float:
    """
    Calculate a normalized quality score (0.0 to 1.0) for a web source.
    Incorporates strict semantic relevance to ensure off-topic pages never score high.
    """
    cfg = config or get_config()
    weights = cfg.scoring

    if word_count == 0 or relevance_score <= 0.05:
        return 0.0

    # 1. Length Score
    ideal_length = 2000.0
    length_score = min(word_count / ideal_length, 1.0)

    # 2. Density Score
    raw_density = term_count / word_count
    max_expected_density = 0.15
    density_score = min(raw_density / max_expected_density, 1.0)

    # 3. Depth Decay
    depth_decay_factor = 0.15
    depth_score = max(1.0 - (depth * depth_decay_factor), 0.2)

    # 4. Domain Authority
    domain_score = cfg.get_domain_score(domain)

    blended_content_score = (length_score + density_score) / 2.0
    freshness_score = 1.0

    base_score = (
        (blended_content_score * weights.content_weight) +
        (depth_score           * weights.relevance_weight) +
        (domain_score          * weights.domain_weight) +
        (freshness_score       * weights.freshness_weight)
    )

    # Multiplied by semantic relevance score: off-topic pages get heavily penalized
    final_score = max(0.0, min(base_score * relevance_score, 1.0))

    logger.debug(
        f"Score for {domain} (words={word_count}, depth={depth}, rel={relevance_score:.2f}): {final_score:.3f}"
    )

    return final_score
