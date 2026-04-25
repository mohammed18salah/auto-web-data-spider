"""
Module: crawler/parser.py
Purpose: HTML parser using BeautifulSoup.
         Extracts clean text content (removing nav, footers, scripts) and
         discovers outbound links for further crawling.
Author: KnowledgeSpider Engine
"""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from knowledge_spider.core.config import Config, get_config
from knowledge_spider.utils.logger import logger


def parse_page(html: str, url: str) -> dict:
    """
    Parse an HTML document to extract its main text and metadata.

    Strips out noise tags (script, style, nav, footer, aside, ads).
    Extracts the title, meta description, and word count.

    Args:
        html: Raw HTML string.
        url:  The source URL of the HTML.

    Returns:
        Dict containing:
          - title: string
          - text: cleaned body text string
          - meta_description: string
          - url: original URL
          - domain: extracted domain
          - word_count: integer word count of the cleaned text
    """
    soup = BeautifulSoup(html, "html.parser")

    # 1. Extract title
    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    # 2. Extract meta description
    meta_desc = ""
    desc_tag = soup.find("meta", attrs={"name": "description"})
    if desc_tag and desc_tag.get("content"):
        meta_desc = desc_tag["content"].strip()

    # 3. Remove noise elements
    noise_tags = [
        "script", "style", "nav", "footer", "header", "aside", 
        "noscript", "iframe", "svg", "canvas"
    ]
    for tag in soup(noise_tags):
        tag.decompose()

    # Try to find the main content container, fallback to body
    main_content = soup.find("main") or soup.find("article") or soup.body
    if not main_content:
        main_content = soup  # absolute fallback

    # 4. Extract text
    # get_text(separator=" ", strip=True) handles spacing between block elements
    raw_text = main_content.get_text(separator=" ", strip=True)
    
    # 5. Clean up excessive whitespace created by block extraction
    clean_text = re.sub(r"\s+", " ", raw_text).strip()
    
    # 6. Count words
    word_count = len(clean_text.split()) if clean_text else 0

    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    logger.debug(f"Parsed {url} -> {word_count} words")

    return {
        "title": title,
        "text": clean_text,
        "meta_description": meta_desc,
        "url": url,
        "domain": domain,
        "word_count": word_count,
    }


def extract_outbound_links(html: str, base_url: str, config: Config | None = None) -> list[str]:
    """
    Extract and resolve all <a href> links from an HTML document.

    If trusted_only is True in config, filters out links to untrusted domains.
    Always filters out links to the exact same URL (self-links) or anchor links.

    Args:
        html: Raw HTML string.
        base_url: The URL where this HTML was fetched (for resolving relative links).
        config: Config instance. Defaults to global singleton.

    Returns:
        A deduplicated list of absolute URLs.
    """
    cfg = config or get_config()
    soup = BeautifulSoup(html, "html.parser")
    
    trusted_only = cfg.crawler.trusted_only
    outbound: set[str] = set()
    
    # Parse the base URL to compare domains
    try:
        base_parsed = urlparse(base_url)
        base_domain = base_parsed.netloc.lower()
        # Drop fragment from base URL for comparison
        base_no_frag = base_url.split('#')[0]
    except Exception:
        base_domain = ""
        base_no_frag = base_url

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"].strip()
        
        # Skip javascript:, mailto:, tel:, etc.
        if href.startswith(("javascript:", "mailto:", "tel:", "data:")):
            continue
            
        # Resolve relative URL
        full_url = urljoin(base_url, href)
        
        # Strip fragment identifier
        full_url_no_frag = full_url.split('#')[0]
        
        # Skip empty or self-links
        if not full_url_no_frag or full_url_no_frag == base_no_frag:
            continue
            
        try:
            parsed_full = urlparse(full_url_no_frag)
            # Must have http/https scheme
            if parsed_full.scheme not in ("http", "https"):
                continue
                
            domain = parsed_full.netloc.lower()
            
            # Domain policy check
            if trusted_only:
                # Allow if it's the SAME domain we are crawling, or in trusted list
                if domain != base_domain and not cfg.is_trusted_domain(domain):
                    continue
                    
            outbound.add(full_url_no_frag)
            
        except Exception:
            continue

    logger.debug(f"Found {len(outbound)} outbound links on {base_url}")
    return list(outbound)
