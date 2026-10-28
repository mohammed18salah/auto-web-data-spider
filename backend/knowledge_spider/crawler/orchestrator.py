"""
Module: crawler/orchestrator.py
Purpose: The main Crawler Orchestrator.
         Ties together DB state, fetcher, parser, deduplicator, NLP,
         and scoring into a robust, autonomous crawl loop.
Author: KnowledgeSpider Engine
"""

from __future__ import annotations

import time
from datetime import datetime

from knowledge_spider.core.config import Config, get_config
from knowledge_spider.core.session import (
    STATUS_RUNNING,
    STATUS_PAUSED,
    load_session,
    save_session_state,
    mark_session_complete,
)
from knowledge_spider.storage.models import SourceModel, TermModel, TopicEdgeModel, TopicModel
from knowledge_spider.storage.database import (
    create_source,
    create_topic,
    update_topic_status,
    create_edge,
    bulk_insert_terms,
    get_topics_by_session,
    get_topic_by_name,
)
from knowledge_spider.query.query_engine import generate_queries, target_sources
from knowledge_spider.crawler.deduplicator import is_new_url, mark_url_visited
from knowledge_spider.crawler.fetcher import fetch_page
from knowledge_spider.crawler.parser import parse_page, extract_outbound_links
from knowledge_spider.nlp.extractor import extract_terms
from knowledge_spider.nlp.summariser import generate_summary
from knowledge_spider.scoring.scorer import calculate_quality_score
from knowledge_spider.utils.hasher import hash_content
from knowledge_spider.utils.logger import logger


class CrawlerOrchestrator:
    """Manages the autonomous crawl loop for a given session."""

    def __init__(self, session_id: str, config: Config | None = None):
        self.session_id = session_id
        self.cfg = config or get_config()
        self.session = load_session(session_id)
        
        # Internal counters to respect config limits
        self.sources_collected = 0
        self.start_time = time.time()
        self._stop_requested = False

        # Seed the queue if this is a fresh session
        self._seed_initial_topic()

    def stop(self) -> None:
        """Signal the orchestrator to stop crawling gracefully."""
        self._stop_requested = True
        logger.info(f"Stop signal received for session {self.session_id[:8]}")

    @property
    def is_stopped(self) -> bool:
        """Return True if a stop signal has been requested."""
        return self._stop_requested

    def _seed_initial_topic(self) -> None:
        """Create the depth=0 root topic if it doesn't exist."""
        existing = get_topic_by_name(self.session_id, self.session.seed_topic)
        if not existing:
            topic = TopicModel(
                session_id=self.session_id,
                name=self.session.seed_topic,
                depth=0,
                relevance_score=1.0,
                status="queued",
                is_seed=True,
            )
            create_topic(topic)
            logger.info(f"Seeded root topic: '{self.session.seed_topic}'")

    def _is_time_up(self) -> bool:
        """Check if the global time limit has been exceeded."""
        elapsed = (time.time() - self.start_time) / 60.0
        return elapsed >= self.cfg.crawler.time_limit_minutes

    def _get_next_topic(self) -> TopicModel | None:
        """Fetch the highest priority queued topic."""
        # get_topics_by_session orders by depth ASC, relevance DESC
        topics = get_topics_by_session(self.session_id)
        for t in topics:
            if t.status == "queued" and t.depth <= self.cfg.crawler.max_depth:
                return t
        return None

    def _process_url(self, url: str, topic: TopicModel) -> None:
        """Fetch, parse, NLP, Score, and Store a single URL."""
        if not is_new_url(url):
            return

        # 1. Fetch
        page_data = fetch_page(url, self.cfg)
        if not page_data:
            mark_url_visited(url) # Prevent re-fetching failed URLs
            return

        # 2. Parse HTML
        parsed = parse_page(page_data["html"], page_data["url"])
        word_count = parsed["word_count"]
        
        if word_count < self.cfg.nlp.min_content_words:
            logger.debug(f"Skipped {url} — only {word_count} words (min {self.cfg.nlp.min_content_words})")
            mark_url_visited(url)
            return

        content_hash = hash_content(parsed["text"])

        # 3. NLP Pipeline
        terms_dict = extract_terms(parsed["text"])
        summary = generate_summary(parsed["text"], self.cfg)

        # 4. Quality Score
        score = calculate_quality_score(
            word_count=word_count,
            term_count=len(terms_dict),
            depth=topic.depth,
            domain=parsed["domain"],
            config=self.cfg,
        )

        # 5. Save Source
        source = SourceModel(
            session_id=self.session_id,
            topic_id=topic.id,
            url=parsed["url"],
            domain=parsed["domain"],
            title=parsed["title"] or parsed["url"],
            content=parsed["text"],
            summary=summary,
            quality_score=score,
            depth_level=topic.depth,
            content_hash=content_hash,
            word_count=word_count,
        )
        
        persisted_source = create_source(source)
        if persisted_source:
            self.sources_collected += 1
            mark_url_visited(parsed["url"])

            # 6. Save Terms
            term_models = [
                TermModel(
                    session_id=self.session_id,
                    topic_id=topic.id,
                    source_id=persisted_source.id,
                    term=t_val,
                    frequency=freq,
                    # We store basic frequency for now, tf-idf can be calculated at export
                    tfidf_score=float(freq) 
                )
                for t_val, freq in terms_dict.items()
            ]
            bulk_insert_terms(term_models)

            # 7. Discover new topics (sub-topics) based on the top extracted terms
            # We only create subtopics if we haven't hit max depth
            if topic.depth < self.cfg.crawler.max_depth:
                self._branch_topics(topic, terms_dict, parsed["url"])

    def _branch_topics(self, parent_topic: TopicModel, terms_dict: dict[str, int], source_url: str) -> None:
        """Create subtopics and edges based on extracted high-frequency terms."""
        # Take the top N terms as new topics
        top_terms = list(terms_dict.items())[:self.cfg.nlp.max_topics_per_page]
        
        for term, freq in top_terms:
            # Score decay: subtopic relevance relies on parent relevance and frequency
            new_relevance = parent_topic.relevance_score * 0.9 
            
            existing = get_topic_by_name(self.session_id, term)
            if not existing:
                new_topic = TopicModel(
                    session_id=self.session_id,
                    name=term,
                    depth=parent_topic.depth + 1,
                    relevance_score=new_relevance,
                    status="queued",
                    is_seed=False,
                )
                existing = create_topic(new_topic)
            
            # Create edge
            create_edge(TopicEdgeModel(
                session_id=self.session_id,
                from_topic=parent_topic.name,
                to_topic=existing.name,
                weight=new_relevance
            ))

    def run(self) -> None:
        """
        Execute the autonomous crawl loop.
        """
        logger.info(f"Starting Orchestrator for session {self.session_id[:8]}...")
        save_session_state(self.session_id, STATUS_RUNNING)

        try:
            while True:
                # Stop check
                if self._stop_requested:
                    logger.info(f"Crawl loop received stop request for session {self.session_id[:8]}")
                    break

                # Limit Checks
                if self.sources_collected >= self.cfg.crawler.max_sources:
                    logger.info(f"Reached max sources limit ({self.cfg.crawler.max_sources}). Stopping.")
                    break
                if self._is_time_up():
                    logger.info(f"Reached time limit ({self.cfg.crawler.time_limit_minutes}m). Stopping.")
                    break

                # Pop queue
                topic = self._get_next_topic()
                if not topic:
                    logger.info("Topic queue is exhausted or max depth reached. Stopping.")
                    break

                logger.info(f"Processing Topic: '{topic.name}' (Depth {topic.depth})")
                update_topic_status(topic.id, "processing")

                # Generate Queries & Search
                queries = generate_queries(topic.name)
                urls = target_sources(topic.name, queries, self.cfg)

                if not urls:
                    logger.warning(f"No URLs found for topic '{topic.name}'")
                    update_topic_status(topic.id, "skipped")
                    continue

                # Process URLs
                for url in urls:
                    if self._stop_requested:
                        logger.info("Stopping URL processing due to cancel signal")
                        break
                    # Break inner loop if limits reached
                    if self.sources_collected >= self.cfg.crawler.max_sources or self._is_time_up():
                        break
                    
                    self._process_url(url, topic)

                # Mark topic done
                update_topic_status(topic.id, "done")
                
                # Periodically save running state
                save_session_state(self.session_id, STATUS_RUNNING)

        except KeyboardInterrupt:
            logger.warning("\nOrchestrator interrupted by user (Ctrl+C).")
            # State gets paused gracefully outside by CLI layer, but we can do nothing here
            raise
        except Exception as e:
            logger.exception(f"Orchestrator fatal error: {e}")
            raise
        finally:
            if self._stop_requested:
                save_session_state(self.session_id, STATUS_PAUSED)
                logger.info(f"Session {self.session_id[:8]} marked as paused following stop request.")
            elif not self._is_time_up() and self.sources_collected < self.cfg.crawler.max_sources:
                mark_session_complete(self.session_id)

        logger.info(f"Orchestrator finished. Collected {self.sources_collected} sources.")
