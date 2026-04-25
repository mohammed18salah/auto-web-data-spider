"""
Module: nlp/extractor.py
Purpose: Term and topic extraction using spaCy.
         Analyzes text to extract Named Entities and Noun Chunks,
         filters out noise (stopwords, punctuation), and returns 
         a frequency distribution of meaningful terms.
Author: KnowledgeSpider Engine
"""

from __future__ import annotations

from collections import Counter
import re

import spacy

from knowledge_spider.utils.logger import logger

# Lazy-loaded spaCy model to avoid huge boot times if NLP isn't hit immediately
_NLP = None


def get_nlp():
    """
    Load and cache the spaCy English model.
    Downloads the model dynamically if it isn't installed.
    """
    global _NLP
    if _NLP is None:
        try:
            logger.debug("Loading spaCy model 'en_core_web_sm'...")
            _NLP = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model 'en_core_web_sm' not found. Attempting download...")
            from spacy.cli import download
            download("en_core_web_sm")
            _NLP = spacy.load("en_core_web_sm")
    return _NLP


def clean_term(term: str) -> str:
    """
    Normalize a term by lowercasing, stripping extra whitespace, 
    and removing leading/trailing punctuation.
    """
    term = term.lower().strip()
    # Remove leading/trailing non-alphanumeric characters
    term = re.sub(r"^[^a-z0-9]+|[^a-z0-9]+$", "", term)
    return term


def is_valid_term(term: str, nlp_vocab) -> bool:
    """
    Check if a term is valid for extraction.
    Must be > 2 chars, not a pure number, and not a registered stopword.
    """
    if len(term) < 3:
        return False
    if term.isnumeric():
        return False
    
    # Check if any individual word in a multi-word phrase is a strict stopword
    # Or if the exact phrase is a stopword
    words = term.split()
    if all(w in nlp_vocab for w in words):
        return False
        
    return True


def extract_terms(text: str, top_n: int = 15) -> dict[str, int]:
    """
    Extract key terms (Named Entities and Noun Chunks) from a block of text.

    Args:
        text:  The clean text content to analyze.
        top_n: Maximum number of terms to return.

    Returns:
        A dictionary mapping the normalized term to its occurrence count.
        e.g. {"domain name system": 5, "ip address": 3}
    """
    if not text or len(text.strip()) == 0:
        return {}

    nlp = get_nlp()
    # Increase max_length for very large web pages (default is 1,000,000)
    nlp.max_length = max(nlp.max_length, len(text) + 10000)

    # Process text
    doc = nlp(text)
    
    # We will collect noun chunks and named entities
    raw_terms = []

    # 1. Named Entities (ORG, PERSON, GPE, PRODUCT, EVENT, WORK_OF_ART)
    allowed_ents = {"ORG", "PERSON", "GPE", "PRODUCT", "EVENT", "WORK_OF_ART", "LOC"}
    for ent in doc.ents:
        if ent.label_ in allowed_ents:
            raw_terms.append(ent.text)

    # 2. Noun Chunks (e.g. "the rapid brown fox" -> "rapid brown fox")
    # We filter out determiners and pronouns via clean_term / is_valid_term
    for chunk in doc.noun_chunks:
        # Avoid huge chunks that are whole sentences
        if len(chunk.text.split()) <= 4:
            raw_terms.append(chunk.text)

    # 3. Clean and filter
    stop_words = nlp.Defaults.stop_words
    term_counts = Counter()

    for rt in raw_terms:
        ct = clean_term(rt)
        if is_valid_term(ct, stop_words):
            term_counts[ct] += 1

    # 4. Return Top N
    most_common = dict(term_counts.most_common(top_n))
    logger.debug(f"Extracted {len(most_common)} top terms from text")
    
    return most_common
