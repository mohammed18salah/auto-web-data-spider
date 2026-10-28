"""
Module: crawler/deduplicator.py
Purpose: Tracks visited URLs to prevent infinite crawl loops and
         redundant fetching. Cross-references against both in-memory
         session cache and the persistent SQLite database.
Author: KnowledgeSpider Engine
"""

from __future__ import annotations

import threading

from knowledge_spider.storage.database import source_url_exists
from knowledge_spider.utils.logger import logger

# Thread-safe in-memory set to track URLs visited in the current process
_SEEN_URLS: set[str] = set()
_LOCK = threading.Lock()


def is_new_url(url: str) -> bool:
    """
    Check if a URL is new (not visited in this session, and not in the DB).

    This prevents infinite loops (A -> B -> A) and ensures we don't 
    re-crawl URLs if the process is resumed or run multiple times.

    Args:
        url: The absolute URL to check.

    Returns:
        True if the URL has never been seen. False if it's already known.
    """
    if not url or not url.strip():
        return False

    url = url.strip()

    # 1. Fast in-memory check
    with _LOCK:
        if url in _SEEN_URLS:
            return False

    # 2. Slower persistent database check
    # (If we paused and resumed, the DB will remember old URLs)
    if source_url_exists(url):
        # Add to memory cache to speed up future checks
        mark_url_visited(url)
        return False

    return True


def mark_url_visited(url: str) -> None:
    """
    Mark a URL as visited in the current session memory.
    
    Args:
        url: The absolute URL to mark.
    """
    if not url:
        return
        
    url = url.strip()
    with _LOCK:
        _SEEN_URLS.add(url)


def clear_deduplicator_cache() -> None:
    """
    Clear the in-memory URL cache.
    Primarily used for testing or when starting a completely fresh session.
    """
    with _LOCK:
        _SEEN_URLS.clear()
        logger.debug("Deduplicator in-memory cache cleared")
