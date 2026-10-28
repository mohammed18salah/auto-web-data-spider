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
    Generate high-precision search queries to deeply explore a topic.

    Args:
        topic: The topic name (e.g. "جامعة الانبار" or "Quantum Computing").

    Returns:
        List of generated query strings, with the exact topic prioritized first.
    """
    from knowledge_spider.utils.lang_detect import detect_script
    
    clean_topic = topic.strip()
    script = detect_script(clean_topic)
    
    if script == "ar":
        templates = [
            "{topic}",
            "ما هو {topic}",
            "شرح {topic}",
            "دليل {topic}",
            "{topic} بروتوكول",
            "أمثلة على {topic}",
            "{topic} ويكيبيديا",
            "معلومات عن {topic}",
        ]
    else:
        templates = [
            "{topic}",
            "what is {topic}",
            "how does {topic} work",
            "{topic} architecture",
            "{topic} tutorial",
            "{topic} overview",
            "{topic} protocol",
            "{topic} specification",
        ]
    
    queries = [t.format(topic=clean_topic) for t in templates]
    seen = set()
    deduped = [q for q in queries if not (q in seen or seen.add(q))]
    logger.debug(f"Generated {len(deduped)} queries for topic '{clean_topic}' (script: {script})")
    return deduped


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
    Execute high-speed search queries via resilient HTTP search and collect deduplicated URLs.
    Prioritizes the exact topic query to get immediate results without waiting.

    Args:
        topic:   The topic being searched.
        queries: List of search queries to execute.
        config:  Config instance. Defaults to global singleton.

    Returns:
        A list of deduplicated URLs found across queries.
    """
    import urllib.parse
    import time
    import httpx
    from bs4 import BeautifulSoup
    
    cfg = config or get_config()
    max_urls = cfg.crawler.max_urls_per_query
    trusted_only = cfg.crawler.trusted_only
    
    collected_urls: set[str] = set()
    logger.info(f"Rapidly targeting sources for '{topic}'...")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
    }

    # Execute queries: exact topic query is first. If it yields sufficient results, return immediately!
    for i, q in enumerate(queries):
        logger.debug(f"Executing web search [{i+1}/{len(queries)}] for: '{q}'")
        try:
            r = httpx.post(
                "https://html.duckduckgo.com/html/",
                data={"q": q},
                headers=headers,
                timeout=4.5,
                follow_redirects=True,
            )
            
            if r.status_code == 200 and r.text:
                soup = BeautifulSoup(r.text, "html.parser")
                added_for_q = 0
                
                # Check both direct url elements and result title links
                for a in soup.select("a.result__url, .result__title a"):
                    if len(collected_urls) >= max_urls:
                        break
                    href = a.get("href", "")
                    actual_url = ""
                    
                    if "/l/?uddg=" in href:
                        try:
                            actual_url = urllib.parse.unquote(href.split("/l/?uddg=")[1].split("&")[0])
                        except Exception:
                            continue
                    elif href.startswith("http") and "duckduckgo.com" not in href:
                        actual_url = href
                    
                    if not actual_url or actual_url in collected_urls:
                        continue
                        
                    domain = extract_domain(actual_url)
                    if not domain or "duckduckgo.com" in domain:
                        continue
                        
                    if trusted_only and not cfg.is_trusted_domain(domain):
                        continue
                        
                    collected_urls.add(actual_url)
                    added_for_q += 1

            # If the primary query already found sufficient URLs, launch immediately!
            if len(collected_urls) >= max_urls or (i == 0 and len(collected_urls) >= 4):
                logger.info(f"Targeting found {len(collected_urls)} URLs on primary query, proceeding immediately.")
                break

            # Brief delay only if configured and more queries needed
            if cfg.crawler.crawl_delay_seconds > 0:
                time.sleep(cfg.crawler.crawl_delay_seconds)
                
        except Exception as e:
            logger.warning(f"Search query '{q}' note: {e}")

    urls = list(collected_urls)
    logger.info(f"Targeting complete: {len(urls)} unique URLs found for '{topic}'")
    return urls
