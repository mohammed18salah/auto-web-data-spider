"""
Module: nlp/summariser.py
Purpose: Bilingual extractive text summarisation using sumy's TextRank.
         Detects Arabic vs English content and picks the correct NLTK tokenizer.
Author: KnowledgeSpider Engine
"""

from __future__ import annotations

import nltk
from sumy.nlp.tokenizers import Tokenizer
from sumy.parsers.plaintext import PlaintextParser
from sumy.summarizers.text_rank import TextRankSummarizer

from knowledge_spider.core.config import Config, get_config
from knowledge_spider.utils.lang_detect import detect_script
from knowledge_spider.utils.logger import logger

_NLTK_INITIALIZED = False


def _ensure_nltk_data():
    global _NLTK_INITIALIZED
    if _NLTK_INITIALIZED:
        return
    try:
        nltk.data.find("tokenizers/punkt_tab")
    except LookupError:
        logger.debug("Downloading NLTK punkt_tab tokenizer...")
        nltk.download("punkt", quiet=True)
        nltk.download("punkt_tab", quiet=True)
    _NLTK_INITIALIZED = True


def generate_summary(text: str, config: Config | None = None) -> str:
    """
    Generate an extractive summary with automatic language detection.

    For Arabic text  → uses sumy Tokenizer("arabic")
    For English text → uses sumy Tokenizer("english")
    For mixed text   → summarises both segments and combines them.

    Args:
        text:   The clean text block to summarize.
        config: Config instance. If None, uses global singleton.

    Returns:
        A string containing the summary. Empty string if text is too short.
    """
    if not text or len(text.strip()) < 50:
        return ""

    cfg = config or get_config()
    sentence_count = getattr(cfg.nlp, "summary_sentences", getattr(cfg.nlp, "summary_sentence_count", 5))

    _ensure_nltk_data()

    script = detect_script(text)

    def _summarise_block(block: str, lang: str) -> str:
        """Inner helper: summarise a single-language text block."""
        if not block or len(block.strip()) < 50:
            return ""
        try:
            # sumy uses 'arabic' / 'english' as tokenizer names
            tokenizer_lang = "arabic" if lang == "ar" else "english"
            parser = PlaintextParser.from_string(block, Tokenizer(tokenizer_lang))
            summarizer = TextRankSummarizer()
            sentences = summarizer(parser.document, sentence_count)
            result = " ".join(str(s) for s in sentences)
            logger.debug(f"[{lang.upper()}] Generated {len(sentences)}-sentence summary")
            return result
        except Exception as e:
            logger.warning(f"Summarisation failed ({lang}): {e}")
            return block[:300] + "..." if len(block) > 300 else block

    if script == "ar":
        return _summarise_block(text, "ar")

    elif script == "en":
        return _summarise_block(text, "en")

    else:  # mixed — split and summarise each, then join
        from knowledge_spider.utils.lang_detect import split_by_language
        segments = split_by_language(text)
        ar_summary = _summarise_block(segments["ar"], "ar")
        en_summary = _summarise_block(segments["en"], "en")
        parts = [p for p in [ar_summary, en_summary] if p]
        return " | ".join(parts)

