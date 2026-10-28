"""
Module: nlp/extractor.py
Purpose: Bilingual (Arabic + English) term extraction using spaCy.
         - English: en_core_web_sm (Named Entities + Noun Chunks)
         - Arabic:  spacy.blank("ar") + regex-based word extraction
         - Mixed pages: splits by script, processes each part separately,
           then merges results with a language tag prefix.
Author: KnowledgeSpider Engine
"""

from __future__ import annotations

import re
from collections import Counter

from knowledge_spider.utils.lang_detect import detect_script, split_by_language
from knowledge_spider.utils.logger import logger

# ── Lazy-loaded models ────────────────────────────────────────────────────────
_NLP_EN = None   # en_core_web_sm
_NLP_AR = None   # spacy.blank("ar") — Arabic tokenizer, no vectors needed


def _get_nlp_en():
    """Load and cache the English spaCy model lazily."""
    global _NLP_EN
    if _NLP_EN is None:
        import spacy
        try:
            _NLP_EN = spacy.load("en_core_web_sm")
            logger.debug("Loaded spaCy model 'en_core_web_sm'")
        except OSError:
            logger.warning("en_core_web_sm not found. Downloading...")
            from spacy.cli import download
            download("en_core_web_sm")
            _NLP_EN = spacy.load("en_core_web_sm")
    return _NLP_EN


def _get_nlp_ar():
    """Load and cache the Arabic blank spaCy model (tokenizer only)."""
    global _NLP_AR
    if _NLP_AR is None:
        _NLP_AR = spacy.blank("ar")
        logger.debug("Loaded spaCy blank Arabic tokenizer")
    return _NLP_AR


# ── Arabic stopwords (common closed-class words) ──────────────────────────────
_AR_STOPWORDS = {
    "في", "من", "إلى", "على", "عن", "مع", "هذا", "هذه", "ذلك", "تلك",
    "هو", "هي", "هم", "هن", "أن", "أو", "و", "ف", "ب", "ل", "ك",
    "قد", "كان", "كانت", "يكون", "التي", "الذي", "الذين", "اللاتي",
    "إن", "إذا", "لم", "لا", "ما", "مما", "بما", "عما", "له", "لها",
    "لهم", "به", "بها", "بهم", "فيه", "فيها", "فيهم", "منه", "منها",
    "عليه", "عليها", "عليهم", "كل", "بعض", "أي", "حتى", "عند", "بعد",
    "قبل", "خلال", "حول", "كما", "أيضا", "فقط", "هناك", "حيث",
}

_AR_WORD_PATTERN = re.compile(r'[\u0600-\u06FF]{3,}')  # Arabic words ≥ 3 chars


def clean_term_en(term: str) -> str:
    """Normalize an English term."""
    term = term.lower().strip()
    term = re.sub(r"^[^a-z0-9]+|[^a-z0-9]+$", "", term)
    return term

clean_term = clean_term_en


def clean_term_ar(term: str) -> str:
    """Normalize an Arabic term (strip diacritics, strip whitespace)."""
    term = term.strip()
    # Remove Arabic diacritics (tashkeel: U+064B → U+065F)
    term = re.sub(r'[\u064B-\u065F]', '', term)
    return term


def _extract_en(text: str, top_n: int) -> dict[str, int]:
    """Extract English terms using spaCy NER + noun chunks."""
    if not text.strip():
        return {}

    nlp = _get_nlp_en()
    nlp.max_length = max(nlp.max_length, len(text) + 10000)
    doc = nlp(text)

    raw_terms = []
    allowed_ents = {"ORG", "PERSON", "GPE", "PRODUCT", "EVENT", "WORK_OF_ART", "LOC"}
    for ent in doc.ents:
        if ent.label_ in allowed_ents:
            raw_terms.append(ent.text)

    for chunk in doc.noun_chunks:
        if len(chunk.text.split()) <= 4:
            raw_terms.append(chunk.text)

    stop_words = nlp.Defaults.stop_words
    counts: Counter = Counter()
    for rt in raw_terms:
        ct = clean_term_en(rt)
        if len(ct) >= 3 and not ct.isnumeric() and ct not in stop_words:
            counts[ct] += 1

    return dict(counts.most_common(top_n))


def _extract_ar(text: str, top_n: int) -> dict[str, int]:
    """
    Extract Arabic terms using high-speed regex tokenization and frequency analysis.
    Executes in under 1ms without requiring heavy NLP model loading overhead.
    """
    if not text.strip():
        return {}

    words = _AR_WORD_PATTERN.findall(text)
    counts: Counter = Counter()
    for w in words:
        word = clean_term_ar(w)
        if (
            len(word) >= 3
            and word not in _AR_STOPWORDS
        ):
            counts[word] += 1

    return dict(counts.most_common(top_n))


def extract_terms(text: str, top_n: int = 15) -> dict[str, int]:
    """
    Bilingual term extraction from Arabic, English, or mixed text.

    Strategy:
      - Detect dominant script of the text block.
      - Arabic → extract Arabic terms only.
      - English → extract English terms only.
      - Mixed → split by language, extract each separately,
                 prefix Arabic terms with 'ar:' for traceability,
                 merge and return top N overall.

    Args:
        text:  Clean text from a web page.
        top_n: Max terms to return per language.

    Returns:
        Dict mapping term → frequency count.
    """
    if not text or not text.strip():
        return {}

    script = detect_script(text)
    logger.debug(f"Text script detected: '{script}'")

    if script == "ar":
        return _extract_ar(text, top_n)

    elif script == "en":
        return _extract_en(text, top_n)

    else:  # mixed
        segments = split_by_language(text)
        en_terms = _extract_en(segments["en"], top_n)
        ar_terms = _extract_ar(segments["ar"], top_n)

        # Prefix Arabic terms so they stay identifiable in the DB
        merged: Counter = Counter(en_terms)
        for term, freq in ar_terms.items():
            merged[f"ar:{term}"] += freq

        logger.debug(
            f"Mixed extraction: {len(en_terms)} EN terms + "
            f"{len(ar_terms)} AR terms"
        )
        return dict(merged.most_common(top_n * 2))
