"""
Module: query/query_engine.py
Purpose: Search query generation and URL targeting.
         Generates pattern-based search queries for a topic, runs them
         through DuckDuckGo, and returns a deduplicated list of URLs.
Author: KnowledgeSpider Engine
"""

from __future__ import annotations

import time
from urllib.parse import urlparse

from duckduckgo_search import DDGS

from knowledge_spider.core.config import Config, get_config
from knowledge_spider.utils.logger import logger


def generate_queries(topic: str) -> list[str]:
    """
    Generate a list of search queries to deeply explore a topic.

    Args:
        topic: The topic name (e.g. "DNS").

    Returns:
        List of generated query strings based on predefined templates.
    """
    from knowledge_spider.utils.lang_detect import detect_script
    
    script = detect_script(topic)
    
    if script == "ar":
        templates = [
            "ما هو {topic}",
            "شرح {topic}",
            "دليل {topic}",
            "{topic} بروتوكول",
            "أمثلة على {topic}",
            "كيف يعمل {topic}",
            "أنواع {topic}",
            "{topic} بالعربي",
        ]
    else:
        templates = [
            "what is {topic}",
            "{topic} explained",
            "{topic} tutorial",
            "{topic} protocol",
            "{topic} examples",
            "how does {topic} work",
            "{topic} types",
            "{topic} RFC",
        ]
    
    queries = [t.format(topic=topic) for t in templates]
    logger.debug(f"Generated {len(queries)} queries for topic '{topic}' (script: {script})")
    return queries


def extract_domain(url: str) -> str:
    """
    Extract the registered domain from a full URL.
    
    Args:
        url: The full URL string.
        
    Returns:
        The network location part of the URL.
    """
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower()
    except Exception:
        return ""


def target_sources(topic: str, queries: list[str], config: Config | None = None) -> list[str]:
    """
    Execute search queries via DuckDuckGo using a real browser (Playwright) 
    and collect deduplicated URLs.

    Args:
        topic:   The topic being searched.
        queries: List of search queries to execute.
        config:  Config instance. Defaults to global singleton.

    Returns:
        A list of deduplicated URLs found across all queries.
    """
    from playwright.sync_api import sync_playwright
    import urllib.parse
    import time
    
    cfg = config or get_config()
    max_urls = cfg.crawler.max_urls_per_query
    trusted_only = cfg.crawler.trusted_only
    
    collected_urls: set[str] = set()
    logger.info(f"Targeting sources for '{topic}' using {len(queries)} queries...")

    import sys
    import asyncio
    
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    with sync_playwright() as p:
        # headless=True so the actual Chrome doesn't pop up!
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        for q in queries:
            logger.debug(f"Executing search in browser: '{q}'")
            try:
                # Use the standard DuckDuckGo search page
                encoded_q = urllib.parse.quote_plus(q)
                search_url = f"https://duckduckgo.com/?q={encoded_q}"
                
                page.goto(search_url, wait_until="domcontentloaded")
                # Wait for search results to appear
                page.wait_for_selector('a[data-testid="result-title-a"]', timeout=10000)
                time.sleep(1) # brief pause to let user see it
                
                # Extract links from the search results
                links = page.query_selector_all('a[data-testid="result-title-a"]')
                
                added_count = 0
                for link in links:
                    if added_count >= max_urls:
                        break
                        
                    href = link.get_attribute("href")
                    if not href or href.startswith("/") or "duckduckgo.com" in href:
                        continue
                        
                    actual_url = href
                    domain = extract_domain(actual_url)
                    
                    if trusted_only and not cfg.is_trusted_domain(domain):
                        continue
                        
                    collected_urls.add(actual_url)
                    added_count += 1
                
                # Sleep briefly based on config
                time.sleep(cfg.crawler.crawl_delay_seconds)
                
            except Exception as e:
                logger.warning(f"Browser search failed for query '{q}': {e}")
        
        browser.close()

    urls = list(collected_urls)
    logger.info(f"Targeting complete: {len(urls)} unique URLs found for '{topic}'")
    return urls
