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

from collections import defaultdict
import threading
from typing import Optional

from knowledge_spider.storage.database import source_url_exists
from knowledge_spider.utils.logger import logger

# Thread-safe in-memory cache of visited URLs per session
_SEEN_URLS_BY_SESSION: dict[str, set[str]] = defaultdict(set)
_SEEN_URLS_GLOBAL: set[str] = set()
_LOCK = threading.Lock()


def is_new_url(url: str, session_id: Optional[str] = None) -> bool:
    """
    Check if a URL is new (not visited in this session, and not in the DB for this session).

    This prevents infinite loops (A -> B -> A) and ensures we don't 
    re-crawl URLs repeatedly within the same session.

    Args:
        url: The absolute URL to check.
        session_id: Optional session UUID to scope check to the current session.

    Returns:
        True if the URL has not been crawled in this session. False if already known.
    """
    if not url or not url.strip():
        return False

    url = url.strip()

    # 1. Fast in-memory check
    with _LOCK:
        if session_id:
            if url in _SEEN_URLS_BY_SESSION[session_id]:
                return False
        else:
            if url in _SEEN_URLS_GLOBAL:
                return False

    # 2. Slower persistent database check for this session
    if source_url_exists(url, session_id=session_id):
        # Add to memory cache to speed up future checks
        mark_url_visited(url, session_id=session_id)
        return False

    return True


def mark_url_visited(url: str, session_id: Optional[str] = None) -> None:
    """
    Mark a URL as visited in the current session memory.
    
    Args:
        url: The absolute URL to mark.
        session_id: Optional session UUID to scope marking.
    """
    if not url:
        return
        
    url = url.strip()
    with _LOCK:
        if session_id:
            _SEEN_URLS_BY_SESSION[session_id].add(url)
        _SEEN_URLS_GLOBAL.add(url)


def clear_deduplicator_cache(session_id: Optional[str] = None) -> None:
    """
    Clear the in-memory URL cache.
    Primarily used for testing or when starting a completely fresh session.
    """
    with _LOCK:
        if session_id and session_id in _SEEN_URLS_BY_SESSION:
            _SEEN_URLS_BY_SESSION[session_id].clear()
        else:
            _SEEN_URLS_BY_SESSION.clear()
            _SEEN_URLS_GLOBAL.clear()
        logger.debug("Deduplicator in-memory cache cleared")
