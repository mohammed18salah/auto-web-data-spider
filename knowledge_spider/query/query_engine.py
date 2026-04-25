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
    logger.debug(f"Generated {len(queries)} queries for topic '{topic}'")
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
    Execute search queries via DuckDuckGo and collect deduplicated URLs.

    Applies `trusted_only` domain filtering if specified in the configuration.
    Delays between queries to avoid rate-limiting.

    Args:
        topic:   The topic being searched.
        queries: List of search queries to execute.
        config:  Config instance. Defaults to global singleton.

    Returns:
        A list of deduplicated URLs found across all queries.
    """
    cfg = config or get_config()
    max_urls = cfg.crawler.max_urls_per_query
    trusted_only = cfg.crawler.trusted_only
    
    collected_urls: set[str] = set()
    logger.info(f"Targeting sources for '{topic}' using {len(queries)} queries...")

    with DDGS() as ddgs:
        for q in queries:
            logger.debug(f"Executing search: '{q}'")
            try:
                # Use duckduckgo-search text search
                results = ddgs.text(q, max_results=max_urls)
                
                for r in results:
                    url = r.get("href")
                    if not url:
                        continue
                        
                    domain = extract_domain(url)
                    
                    if trusted_only and not cfg.is_trusted_domain(domain):
                        logger.debug(f"Dropped untrusted URL: {url}")
                        continue
                        
                    collected_urls.add(url)
                
                # Sleep briefly to avoid DDG rate limits
                time.sleep(cfg.crawler.crawl_delay_seconds)
                
            except Exception as e:
                logger.warning(f"Search failed for query '{q}': {e}")
                time.sleep(cfg.crawler.crawl_delay_seconds * 2)

    urls = list(collected_urls)
    logger.info(f"Targeting complete: {len(urls)} unique URLs found for '{topic}'")
    return urls
