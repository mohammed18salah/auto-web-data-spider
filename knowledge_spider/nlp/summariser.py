"""
Module: nlp/summariser.py
Purpose: Extractive text summarisation using sumy's TextRank.
         Condenses long HTML text into a concise summary defined by
         the config (default 3 sentences).
Author: KnowledgeSpider Engine
"""

from __future__ import annotations

import nltk
from sumy.nlp.tokenizers import Tokenizer
from sumy.parsers.plaintext import PlaintextParser
from sumy.summarizers.text_rank import TextRankSummarizer

from knowledge_spider.core.config import Config, get_config
from knowledge_spider.utils.logger import logger

_NLTK_INITIALIZED = False


def _ensure_nltk_data():
    """
    Ensure the required NLTK 'punkt' and 'punkt_tab' tokenizers are available.
    Downloads them silently if missing.
    """
    global _NLTK_INITIALIZED
    if _NLTK_INITIALIZED:
        return

    try:
        # Check if already installed
        nltk.data.find("tokenizers/punkt_tab")
    except LookupError:
        logger.debug("Downloading NLTK punkt_tab tokenizer...")
        nltk.download("punkt", quiet=True)
        nltk.download("punkt_tab", quiet=True)
    
    _NLTK_INITIALIZED = True


def generate_summary(text: str, config: Config | None = None) -> str:
    """
    Generate an extractive summary of the provided text.

    Args:
        text:   The clean text block to summarize.
        config: Config instance. If None, uses global singleton.

    Returns:
        A string containing the summary (sentences joined by space).
        Returns an empty string if text is too short or empty.
    """
    if not text or len(text.strip()) < 50:
        return ""

    cfg = config or get_config()
    sentence_count = cfg.nlp.summary_sentences

    _ensure_nltk_data()

    try:
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = TextRankSummarizer()
        
        # Extract the top N sentences
        summary_sentences = summarizer(parser.document, sentence_count)
        
        # Rejoin into a single string
        summary = " ".join([str(sentence) for sentence in summary_sentences])
        logger.debug(f"Generated {len(summary_sentences)}-sentence summary from text")
        
        return summary
    except Exception as e:
        logger.warning(f"Summarisation failed: {e}")
        # Fallback to simple truncation if sumy fails
        return text[:300] + "..." if len(text) > 300 else text
