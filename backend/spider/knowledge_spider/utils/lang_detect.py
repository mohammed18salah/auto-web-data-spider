"""
Module: utils/lang_detect.py
Purpose: Language detection and text splitting for bilingual Arabic/English content.
         Uses regex (no external model needed for Arabic — Unicode is reliable)
         and langdetect for non-Arabic content.
Author: KnowledgeSpider Engine
"""

from __future__ import annotations

import re
from knowledge_spider.utils.logger import logger

# Arabic Unicode block: U+0600 → U+06FF
_AR_PATTERN = re.compile(r'[\u0600-\u06FF]+')
_EN_PATTERN = re.compile(r'[A-Za-z]{3,}')   # ≥3 chars to skip noise


def detect_script(text: str) -> str:
    """
    Detect dominant script in a text sample.

    Returns:
        'ar'    — Arabic dominant (>40% Arabic characters)
        'en'    — English dominant
        'mixed' — Contains meaningful amounts of both
    """
    if not text:
        return "en"

    total_chars = len(text.replace(" ", ""))
    if total_chars == 0:
        return "en"

    ar_chars = len("".join(_AR_PATTERN.findall(text)))
    en_chars = len("".join(_EN_PATTERN.findall(text)))

    ar_ratio = ar_chars / total_chars
    en_ratio = en_chars / total_chars

    if ar_ratio > 0.4 and en_ratio > 0.15:
        return "mixed"
    elif ar_ratio > 0.25:
        return "ar"
    else:
        return "en"


def split_by_language(text: str) -> dict[str, str]:
    """
    Split a paragraph block into Arabic and English segments.

    Splits on sentence/line boundaries then classifies each segment.
    Returns a dict with keys 'ar' and 'en' containing the joined text.

    Args:
        text: Raw body text from a web page (may be mixed).

    Returns:
        {'ar': 'Arabic text...', 'en': 'English text...'}
    """
    # Split into sentence-like chunks (period, newline, Arabic sentence end ۔)
    chunks = re.split(r'(?<=[.!?\n۔])\s+', text)

    ar_segments: list[str] = []
    en_segments: list[str] = []

    for chunk in chunks:
        chunk = chunk.strip()
        if len(chunk) < 10:
            continue
        script = detect_script(chunk)
        if script == "ar":
            ar_segments.append(chunk)
        elif script == "en":
            en_segments.append(chunk)
        else:   # mixed — add to both
            ar_segments.append(chunk)
            en_segments.append(chunk)

    return {
        "ar": " ".join(ar_segments),
        "en": " ".join(en_segments),
    }
