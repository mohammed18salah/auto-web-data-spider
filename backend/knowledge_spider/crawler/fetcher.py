"""
Module: crawler/fetcher.py
Purpose: HTTP fetcher with hybrid strategy (fast httpx with Playwright fallback).
         Provides robust page fetching with timeout enforcement, rate limiting,
         and error recovery.
Author: KnowledgeSpider Engine
"""

from __future__ import annotations

import sys
import asyncio
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx

from knowledge_spider.core.config import Config, get_config
from knowledge_spider.crawler.robots import is_crawl_allowed
from knowledge_spider.utils.logger import logger


def fetch_page(url: str, config: Optional[Config] = None) -> Optional[Dict[str, Any]]:
    """
    Fetch a webpage using a high-performance hybrid strategy:
    1. Fast HTTP request via httpx (handles 95%+ of sites in milliseconds).
    2. Playwright Chromium fallback for complex JS-rendered web applications.

    Args:
        url: The full URL to fetch.
        config: Config instance (defaults to global singleton).

    Returns:
        A dict containing url, status_code, html, headers, and fetched_at.
        Returns None if fetch fails.
    """
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    cfg = config or get_config()

    # 1. robots.txt check
    if not is_crawl_allowed(url):
        logger.warning(f"Fetch skipped: blocked by robots.txt -> {url}")
        return None

    # 2. Rate limiting (sleep)
    if cfg.crawler.crawl_delay_seconds > 0:
        time.sleep(cfg.crawler.crawl_delay_seconds)

    logger.debug(f"Fetching: {url}")

    headers = {
        "User-Agent": "KnowledgeSpiderBot/1.0 (https://github.com/mohammed18salah/data-spider; contact@example.com) Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
    }

    # Step 1: Fast HTTP request via httpx
    needs_playwright = False
    try:
        r = httpx.get(
            url,
            headers=headers,
            timeout=4.0,
            follow_redirects=True,
            verify=False,
        )
        if r.status_code < 400 and r.text and len(r.text.strip()) > 300:
            return {
                "url": str(r.url),
                "status_code": r.status_code,
                "html": r.text,
                "headers": dict(r.headers),
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }
        elif r.status_code < 400:
            needs_playwright = True
    except Exception as http_err:
        logger.debug(f"HTTP fetch failed for {url} ({http_err})")
        return None

    # Step 2: Headless Playwright fallback only for empty SPAs (fast 4s timeout)
    if needs_playwright:
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    viewport={"width": 1280, "height": 720},
                    user_agent=headers["User-Agent"],
                )
                page = context.new_page()
                response = page.goto(url, wait_until="domcontentloaded", timeout=4000)

                if not response or response.status >= 400:
                    browser.close()
                    return None

                html_content = page.content()
                final_url = page.url
                status = response.status
                browser.close()

                return {
                    "url": final_url,
                    "status_code": status,
                    "html": html_content,
                    "headers": {},
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                }
        except Exception as e:
            logger.warning(f"Error fetching {url}: {e}")

    return None
