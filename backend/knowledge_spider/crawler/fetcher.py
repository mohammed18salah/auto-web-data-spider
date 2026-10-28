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
from datetime import datetime, timezone
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
    Fetch a webpage synchronously via a real browser (Playwright) with safety constraints.
    This opens a visible browser so the user can watch the crawling process.

    Args:
        url: The full URL to fetch.
        config: Config instance (defaults to global singleton).

    Returns:
        A dict containing:
          - url: Final URL
          - status_code: HTTP status (default 200 for browser if successful)
          - html: The text content
          - headers: Empty dict (not strictly tracked in simple playwright mode)
          - fetched_at: ISO timestamp
        Returns None if fetch fails.
    """
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
    import sys
    import asyncio
    
    # Fix for Windows asyncio loop policy
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    cfg = config or get_config()

    # 1. robots.txt check
    if not is_crawl_allowed(url):
        logger.warning(f"Fetch skipped: blocked by robots.txt -> {url}")
        return None

    # 2. Rate limiting (sleep)
    if cfg.crawler.crawl_delay_seconds > 0:
        time.sleep(cfg.crawler.crawl_delay_seconds)

    logger.debug(f"Browsing to: {url}")
    
    try:
        with sync_playwright() as p:
            # headless=True so the actual Chrome doesn't pop up!
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            # Go to the URL
            response = page.goto(url, wait_until="domcontentloaded", timeout=15000)
            
            if not response:
                logger.warning(f"No response from {url}")
                browser.close()
                return None
                
            # Sleep a moment to let the user see the page and let JS load
            time.sleep(2)
            
            html_content = page.content()
            final_url = page.url
            status = response.status

            browser.close()

            # Ensure we don't process binary data (though playwright handles text pages best)
            if status >= 400:
                logger.warning(f"HTTP error {status} fetching {url}")
                return None

            return {
                "url": final_url,
                "status_code": status,
                "html": html_content,
                "headers": {},
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }

    except PlaywrightTimeoutError:
        logger.warning(f"Timeout browsing to {url}")
    except Exception as e:
        logger.error(f"Unexpected error browsing {url}: {e}")

    return None
