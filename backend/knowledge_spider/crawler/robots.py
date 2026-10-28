"""
Module: crawler/robots.py
Purpose: robots.txt compliance checker.
         Maintains an in-memory cache of RobotFileParser instances per domain
         so we don't repeatedly fetch the same rules. Supports config toggling.
Author: KnowledgeSpider Engine
"""

from __future__ import annotations

import urllib.request
import urllib.robotparser
from urllib.error import URLError, HTTPError
from urllib.parse import urlparse

from knowledge_spider.core.config import get_config
from knowledge_spider.utils.logger import logger

# ── In-memory cache of RobotFileParser instances ─────────────────────────────
# Key: lowercased scheme://netloc (e.g. "https://en.wikipedia.org")
# Value: RobotFileParser initialized with the fetched robots.txt
_ROBOTS_CACHE: dict[str, urllib.robotparser.RobotFileParser] = {}


def _get_robots_url(url: str) -> str:
    """
    Construct the robots.txt URL for a given target URL.

    Args:
        url: The target URL (e.g. "https://example.com/some/path").

    Returns:
        The URL pointing to the domain's robots.txt.
    """
    parsed = urlparse(url)
    scheme = parsed.scheme or "https"
    netloc = parsed.netloc
    return f"{scheme}://{netloc}/robots.txt"


def _fetch_robot_parser(base_url: str) -> urllib.robotparser.RobotFileParser | None:
    """
    Fetch and parse the robots.txt for a given base URL rapidly via httpx.

    Args:
        base_url: The scheme://netloc root of the site.

    Returns:
        A populated RobotFileParser, or None if fetching failed or timed out.
    """
    import httpx

    robots_url = f"{base_url}/robots.txt"
    parser = urllib.robotparser.RobotFileParser()
    parser.set_url(robots_url)
    
    try:
        r = httpx.get(
            robots_url,
            headers={"User-Agent": "KnowledgeSpiderBot/1.0 (https://github.com/knowledge-spider; contact@example.com)"},
            timeout=3.0,
            follow_redirects=True,
            verify=False,
        )
        if r.status_code == 200 and r.text:
            lines = r.text.splitlines()
            parser.parse(lines)
            logger.debug(f"Fetched and parsed robots.txt for {base_url}")
            return parser
        return None
    except Exception:
        # If robots.txt times out (>1.5s) or fails, don't stall the crawler
        return None


def is_crawl_allowed(url: str, user_agent: str = "*") -> bool:
    """
    Determine if the given URL is allowed to be crawled according to robots.txt.

    Respects the `respect_robots` toggle in config.toml.
    Caches rules per domain.

    Args:
        url: The full URL to check.
        user_agent: The user agent to verify against (default: "*").

    Returns:
        True if crawling is allowed, False if blocked.
    """
    cfg = get_config()
    if not cfg.crawler.respect_robots:
        return True

    parsed = urlparse(url)
    if not parsed.netloc:
        return False  # Invalid URL

    scheme = parsed.scheme or "https"
    base_url = f"{scheme}://{parsed.netloc}".lower()

    # Check cache first
    if base_url not in _ROBOTS_CACHE:
        parser = _fetch_robot_parser(base_url)
        # Store even if None (to avoid re-fetching on failure)
        _ROBOTS_CACHE[base_url] = parser

    parser = _ROBOTS_CACHE[base_url]

    # If we couldn't fetch robots.txt (e.g., 404), assume allowed
    if parser is None:
        return True

    allowed = parser.can_fetch(user_agent, url)
    if not allowed:
        logger.debug(f"robots.txt blocked access to: {url}")

    return allowed


def clear_robots_cache() -> None:
    """
    Clear the in-memory robots.txt cache.
    Primarily used for testing or when starting a fresh, long-running session.
    """
    _ROBOTS_CACHE.clear()
    logger.debug("Robots cache cleared")
