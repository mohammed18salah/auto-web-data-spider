"""
Module: crawler/fetcher.py
Purpose: HTTP fetcher using httpx.
         Provides robust page fetching with user-agent rotation, 
         timeout enforcement, rate limiting (delays), and robots.txt checks.
Author: KnowledgeSpider Engine
"""

from __future__ import annotations

import random
import time
from datetime import datetime
from typing import Any, Dict, Optional

import httpx

from knowledge_spider.core.config import Config, get_config
from knowledge_spider.crawler.robots import is_crawl_allowed
from knowledge_spider.utils.logger import logger

# ── User-Agent Pool ──────────────────────────────────────────────────────────
# Wikipedia and other strict sites require bot identification to avoid 403s.
USER_AGENTS = [
    "KnowledgeSpiderBot/1.0 (Python; +https://github.com/project) Mozilla/5.0",
]


def fetch_page(url: str, config: Optional[Config] = None) -> Optional[Dict[str, Any]]:
    """
    Fetch a webpage synchronously via httpx with safety constraints.

    Process:
    1. Check robots.txt (if enabled in config).
    2. Sleep for crawl_delay_seconds to avoid rate limits.
    3. Rotate User-Agent.
    4. Fetch page with a 15-second timeout and following redirects.
    5. Return a structured dictionary with HTML and metadata.

    Args:
        url: The full URL to fetch.
        config: Config instance (defaults to global singleton).

    Returns:
        A dict containing:
          - url: Final redirected URL
          - status_code: HTTP status
          - html: The text content
          - headers: Response headers dict
          - fetched_at: ISO timestamp
        Returns None if fetch fails (404, blocked, timeout, etc.)
    """
    cfg = config or get_config()

    # 1. robots.txt check
    if not is_crawl_allowed(url):
        logger.warning(f"Fetch skipped: blocked by robots.txt -> {url}")
        return None

    # 2. Rate limiting (sleep)
    if cfg.crawler.crawl_delay_seconds > 0:
        time.sleep(cfg.crawler.crawl_delay_seconds)

    # 3. User-Agent rotation
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    # 4. Fetch
    logger.debug(f"Fetching: {url}")
    try:
        with httpx.Client(follow_redirects=True, timeout=15.0) as client:
            response = client.get(url, headers=headers)
            
            # Raise for 4xx/5xx errors
            response.raise_for_status()

            # Ensure we got HTML text (ignore PDFs, images, etc.)
            content_type = response.headers.get("Content-Type", "").lower()
            if "text/html" not in content_type and "text/plain" not in content_type:
                logger.warning(f"Fetch skipped: non-text content-type '{content_type}' at {url}")
                return None

            return {
                "url": str(response.url),
                "status_code": response.status_code,
                "html": response.text,
                "headers": dict(response.headers),
                "fetched_at": datetime.utcnow().isoformat(),
            }

    except httpx.HTTPStatusError as e:
        logger.warning(f"HTTP error {e.response.status_code} fetching {url}: {e}")
    except httpx.TimeoutException:
        logger.warning(f"Timeout fetching {url}")
    except httpx.RequestError as e:
        logger.warning(f"Request error fetching {url}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error fetching {url}: {e}")

    return None
