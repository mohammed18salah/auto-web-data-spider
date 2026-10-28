"""
Module: query/query_engine.py
Purpose: High-precision search query generation and resilient URL targeting.
         Generates compound, entity-aware search queries, queries multiple
         providers (DuckDuckGo, Wikipedia API, CrossRef Academic API),
         and filters candidates with strict semantic relevance.
Author: KnowledgeSpider Engine
"""

from __future__ import annotations

import re
import time
from urllib.parse import urlparse, quote, unquote

import httpx
from bs4 import BeautifulSoup

from knowledge_spider.core.config import Config, get_config
from knowledge_spider.scoring.scorer import compute_semantic_relevance, COMMERCIAL_BLACKLIST_DOMAINS
from knowledge_spider.utils.lang_detect import detect_script
from knowledge_spider.utils.logger import logger


def generate_queries(topic: str, seed_topic: str | None = None) -> list[str]:
    """
    Generate high-precision, entity-aware search queries to deeply explore a topic.
    Avoids low-quality generic templates and enforces exact phrase quotes for compound entities.
    """
    clean_topic = re.sub(r'\s+', ' ', topic.strip())
    script = detect_script(clean_topic)

    queries: list[str] = [clean_topic]

    if script == "ar":
        academic_titles = ["دكتور", "الدكتور", "د.", "د/", "أستاذ", "الاستاذ", "أ.د", "بروفيسور", "مهندس"]
        institution_indicators = ["جامعة", "كلية", "معهد", "مستشفى", "مركز", "أكاديمية"]

        topic_no_title = clean_topic
        for t in academic_titles:
            topic_no_title = re.sub(rf'^{re.escape(t)}\s+', '', topic_no_title, flags=re.IGNORECASE)

        has_inst = any(inst in clean_topic for inst in institution_indicators) or "انبار" in clean_topic or "الأنبار" in clean_topic

        if has_inst:
            parts = re.split(r'\s+(?=جامعة|كلية|معهد|مستشفى|مركز)', topic_no_title)
            if len(parts) >= 2:
                person_part = parts[0].strip()
                inst_part = " ".join(parts[1:]).strip()
                queries.append(f'"{person_part}" "{inst_part}"')
                queries.append(f'"{person_part}" {inst_part}')
                queries.append(f'{person_part} "{inst_part}"')
                if "انبار" in inst_part or "الأنبار" in inst_part:
                    queries.append(f'"{person_part}" site:uoanbar.edu.iq')
                    queries.append(f'"{person_part}" site:edu.iq')
                queries.append(f'السيرة الذاتية "{person_part}" {inst_part}')
                queries.append(f'أبحاث "{person_part}" {inst_part}')
            else:
                queries.append(f'"{clean_topic}"')
                if "انبار" in clean_topic or "الأنبار" in clean_topic:
                    queries.append(f'{clean_topic} site:uoanbar.edu.iq')
                    queries.append(f'كليات {clean_topic}')
                    queries.append(f'دليل {clean_topic}')
                else:
                    queries.append(f'دليل {clean_topic}')
                    queries.append(f'معلومات عن {clean_topic}')
        else:
            queries.append(f'"{clean_topic}"')
            queries.append(f'أبحاث {clean_topic}')
            queries.append(f'معلومات عن {clean_topic}')
    else:
        queries.append(f'"{clean_topic}"')
        queries.append(f'{clean_topic} overview')
        queries.append(f'{clean_topic} research papers')
        queries.append(f'{clean_topic} official guide')

    seen = set()
    deduped = [q for q in queries if not (q in seen or seen.add(q))]
    logger.debug(f"Generated {len(deduped)} smart queries for '{clean_topic}'")
    return deduped


def extract_domain(url: str) -> str:
    """Extract the registered network domain from a full URL."""
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower()
    except Exception:
        return ""


def _query_wikipedia_api(query: str, lang: str = "ar") -> list[str]:
    """Query Wikipedia OpenSearch API for direct verified encyclopedic links."""
    urls = []
    try:
        endpoint = f"https://{lang}.wikipedia.org/w/api.php"
        headers = {"User-Agent": "KnowledgeSpider/2.0 (research crawler; contact@spider.org)"}
        params = {"action": "opensearch", "format": "json", "limit": "5", "search": query}
        with httpx.Client(timeout=4.0) as client:
            resp = client.get(endpoint, params=params, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                if len(data) >= 4 and isinstance(data[3], list):
                    urls.extend(data[3])
    except Exception as e:
        logger.debug(f"Wikipedia API lookup note: {e}")
    return urls


def _query_crossref_api(query: str) -> list[str]:
    """Query CrossRef API for peer-reviewed academic papers and faculty publications."""
    urls = []
    try:
        endpoint = "https://api.crossref.org/works"
        headers = {"User-Agent": "KnowledgeSpider/2.0 (Academic researcher; mailto:contact@spider.org)"}
        params = {"rows": "6", "query": query}
        with httpx.Client(timeout=4.5) as client:
            resp = client.get(endpoint, params=params, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("message", {}).get("items", [])
                for it in items:
                    u = it.get("URL")
                    if u and u.startswith("http"):
                        urls.append(u)
    except Exception as e:
        logger.debug(f"CrossRef API lookup note: {e}")
    return urls


def target_sources(topic: str, queries: list[str], config: Config | None = None) -> list[str]:
    """
    Execute multi-source intelligent search queries across web search,
    Wikipedia, and academic repositories with pre-filtering to prevent topic drift.
    """
    cfg = config or get_config()
    max_urls = cfg.crawler.max_urls_per_query
    trusted_only = cfg.crawler.trusted_only

    collected_urls: list[str] = []
    seen_urls: set[str] = set()

    def add_candidate(url: str, title: str = "", snippet: str = ""):
        if not url or url in seen_urls or len(collected_urls) >= max_urls:
            return
        domain = extract_domain(url)
        if not domain:
            return
        for bad in COMMERCIAL_BLACKLIST_DOMAINS:
            if bad in domain:
                return
        if trusted_only and not cfg.is_trusted_domain(domain):
            return

        # Pre-filter candidate with semantic relevance
        rel_score, _ = compute_semantic_relevance(
            seed_topic=topic,
            title=title,
            url=url,
            content=snippet,
            domain=domain
        )
        if rel_score <= 0.0:
            return

        seen_urls.add(url)
        collected_urls.append(url)

    logger.info(f"Rapidly targeting high-precision sources for '{topic}'...")

    # Channel 1: Wikipedia Verified Entity Search
    wiki_urls = _query_wikipedia_api(topic, lang="ar")
    if not wiki_urls:
        wiki_urls = _query_wikipedia_api(topic, lang="en")
    for w_url in wiki_urls:
        add_candidate(w_url, title=topic)

    # Channel 2: Academic & Research Repositories (if topic involves university/research/faculty)
    is_academic = any(k in topic for k in ["دكتور", "جامعة", "كلية", "أبحاث", "استاذ", "University", "Dr."])
    if is_academic:
        crossref_urls = _query_crossref_api(topic)
        for cr_url in crossref_urls:
            add_candidate(cr_url, title=topic)

    # Channel 3: Resilient Web Search (DuckDuckGo HTML + Lite)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
    }

    for i, q in enumerate(queries):
        if len(collected_urls) >= max_urls:
            break

        logger.debug(f"Executing web search [{i+1}/{len(queries)}] for: '{q}'")
        try:
            with httpx.Client(timeout=4.5, follow_redirects=True, headers=headers) as client:
                resp = None
                try:
                    resp = client.post("https://html.duckduckgo.com/html/", data={"q": q})
                except Exception:
                    # Fallback to lite endpoint
                    try:
                        resp = client.post("https://lite.duckduckgo.com/lite/", data={"q": q})
                    except Exception:
                        pass

                if resp and resp.status_code == 200 and resp.text:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    for res_elem in soup.select(".result, tr"):
                        if len(collected_urls) >= max_urls:
                            break
                        link_tag = res_elem.select_one(".result__title a, a.result-link, .result__url")
                        snip_tag = res_elem.select_one(".result__snippet, .result-snippet")
                        if not link_tag:
                            continue

                        href = link_tag.get("href", "")
                        actual_url = ""
                        if "/l/?uddg=" in href:
                            try:
                                actual_url = unquote(href.split("/l/?uddg=")[1].split("&")[0])
                            except Exception:
                                continue
                        elif href.startswith("http") and "duckduckgo.com" not in href:
                            actual_url = href

                        title_text = link_tag.get_text(strip=True)
                        snip_text = snip_tag.get_text(strip=True) if snip_tag else ""
                        add_candidate(actual_url, title=title_text, snippet=snip_text)

        except Exception as e:
            logger.warning(f"Web search query '{q}' note: {e}")

        if len(collected_urls) >= max_urls or (i == 0 and len(collected_urls) >= 5):
            break

    logger.info(f"Targeting complete: {len(collected_urls)} verified relevant URLs found for '{topic}'")
    return collected_urls
