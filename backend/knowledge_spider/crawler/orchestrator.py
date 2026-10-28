"""
Module: crawler/orchestrator.py
Purpose: The main Crawler Orchestrator.
         Ties together DB state, fetcher, parser, deduplicator, NLP,
         and scoring into a robust, autonomous crawl loop with live state tracking.
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
from knowledge_spider.crawler.parser import parse_page
from knowledge_spider.nlp.extractor import extract_terms
from knowledge_spider.nlp.summariser import generate_summary
from knowledge_spider.scoring.scorer import calculate_quality_score
from knowledge_spider.utils.hasher import hash_content
from knowledge_spider.utils.logger import logger


class CrawlerOrchestrator:
    """Manages the autonomous crawl loop for a given session with real-time UI telemetry."""

    def __init__(self, session_id: str, config: Config | None = None):
        self.session_id = session_id
        self.cfg = config or get_config()
        self.session = load_session(session_id)
        
        # Internal counters to respect config limits
        self.sources_collected = 0
        self.start_time = time.time()
        self._stop_requested = False

        # Live telemetry properties for UI display
        self.current_url: str = ""
        self.current_title: str = ""
        self.current_domain: str = ""
        self.current_summary: str = ""
        self.current_score: float = 0.0
        self.live_logs: list[dict] = []
        self.stop_reason: str = ""
        self.is_finished: bool = False

        # Seed the queue if this is a fresh session
        self._seed_initial_topic()

    def add_log(self, log_type: str, message: str) -> None:
        """Add a structured timestamped log for frontend display."""
        entry = {
            "time": datetime.now().strftime("%I:%M:%S %p"),
            "type": log_type,
            "message": message,
        }
        self.live_logs.append(entry)
        if len(self.live_logs) > 60:
            self.live_logs = self.live_logs[-60:]

    def get_live_state(self) -> dict:
        """Expose current telemetry for live UI polling."""
        return {
            "current_url": self.current_url,
            "current_title": self.current_title,
            "current_domain": self.current_domain,
            "current_summary": self.current_summary,
            "current_score": self.current_score,
            "sources_collected": self.sources_collected,
            "logs": list(self.live_logs),
            "stop_reason": self.stop_reason,
            "is_finished": self.is_finished,
        }

    def stop(self) -> None:
        """Signal the orchestrator to stop crawling gracefully."""
        self._stop_requested = True
        self.stop_reason = "تم الإيقاف يدوياً بناءً على طلب المستخدم"
        self.add_log("sys", "تم استلام أمر إيقاف عملية الزحف من المستخدم...")
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
        topics = get_topics_by_session(self.session_id)
        for t in topics:
            if t.status == "queued" and t.depth <= self.cfg.crawler.max_depth:
                return t
        return None

    def _process_url(self, url: str, topic: TopicModel) -> None:
        """Fetch, parse, NLP, Score, and Store a single URL."""
        if not is_new_url(url):
            return

        self.current_url = url
        self.add_log("sys", f"جاري استعراض وتحميل: {url[:70]}")

        # 1. Fetch
        page_data = fetch_page(url, self.cfg)
        if not page_data:
            mark_url_visited(url)
            return

        # 2. Parse HTML
        parsed = parse_page(page_data["html"], page_data["url"])
        word_count = parsed["word_count"]
        
        if word_count < self.cfg.nlp.min_content_words:
            logger.debug(f"Skipped {url} — only {word_count} words")
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

            self.current_title = source.title
            self.current_domain = source.domain
            self.current_summary = source.summary or ""
            self.current_score = score
            self.add_log("success", f"تم تحليل وحفظ: {source.title[:45]} (جودة: {int(score * 100)}%)")

            # 6. Save Terms
            term_models = [
                TermModel(
                    session_id=self.session_id,
                    topic_id=topic.id,
                    source_id=persisted_source.id,
                    term=t_val,
                    frequency=freq,
                    tfidf_score=float(freq) 
                )
                for t_val, freq in terms_dict.items()
            ]
            bulk_insert_terms(term_models)

            # 7. Discover new topics (sub-topics) based on the top extracted terms
            if topic.depth < self.cfg.crawler.max_depth:
                self._branch_topics(topic, terms_dict, parsed["url"])

    def _branch_topics(self, parent_topic: TopicModel, terms_dict: dict[str, int], source_url: str) -> None:
        """Create subtopics and edges based on extracted high-frequency terms."""
        top_terms = list(terms_dict.items())[:self.cfg.nlp.max_topics_per_page]
        
        for term, freq in top_terms:
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
            
            create_edge(TopicEdgeModel(
                session_id=self.session_id,
                from_topic=parent_topic.name,
                to_topic=existing.name,
                weight=new_relevance
            ))

    def run(self) -> None:
        """Execute the autonomous crawl loop."""
        logger.info(f"Starting Orchestrator for session {self.session_id[:8]}...")
        save_session_state(self.session_id, STATUS_RUNNING)
        self.add_log("info", f"بدء الزحف الذكي لموضوع: {self.session.seed_topic}")

        try:
            while True:
                # Stop check
                if self._stop_requested:
                    self.stop_reason = "تم إيقاف عملية الزحف يدوياً بواسطة المستخدم"
                    logger.info(f"Crawl loop received stop request for session {self.session_id[:8]}")
                    break

                # Limit Checks
                if self.sources_collected >= self.cfg.crawler.max_sources:
                    self.stop_reason = f"تم الوصول إلى الحد الأقصى للمصادر المحدد ({self.cfg.crawler.max_sources} مصادر)"
                    logger.info(f"Reached max sources limit ({self.cfg.crawler.max_sources}). Stopping.")
                    self.add_log("success", f"تم اكتمال الزحف: تم الوصول إلى الحد الأقصى المطلوب للمصادر ({self.cfg.crawler.max_sources} مصادر).")
                    break

                if self._is_time_up():
                    self.stop_reason = f"تم انتهاء المهلة الزمنية المحددة للزحف ({self.cfg.crawler.time_limit_minutes} دقيقة)"
                    logger.info(f"Reached time limit ({self.cfg.crawler.time_limit_minutes}m). Stopping.")
                    self.add_log("info", f"تم إنهاء الزحف: انتهت المهلة الزمنية المحددة ({self.cfg.crawler.time_limit_minutes} دقيقة).")
                    break

                # Pop queue
                topic = self._get_next_topic()
                if not topic:
                    self.stop_reason = f"اكتمل استكشاف جميع الموضوعات والروابط المستهدفة ({self.sources_collected} مصادر)"
                    logger.info("Topic queue is exhausted or max depth reached. Stopping.")
                    self.add_log("success", f"اكتمل استكشاف شجرة الموضوعات بالكامل! تم جمع وفهرسة {self.sources_collected} مصادر.")
                    break

                logger.info(f"Processing Topic: '{topic.name}' (Depth {topic.depth})")
                self.add_log("sys", f"استهداف موضوع: '{topic.name}' (المستوى {topic.depth})...")
                update_topic_status(topic.id, "processing")

                # Generate Queries & Search
                queries = generate_queries(topic.name)
                urls = target_sources(topic.name, queries, self.cfg)

                if not urls:
                    logger.warning(f"No URLs found for topic '{topic.name}'")
                    self.add_log("info", f"لم يتم العثور على روابط ويب إضافية لـ '{topic.name}'.")
                    update_topic_status(topic.id, "skipped")
                    continue

                self.add_log("info", f"تم العثور على {len(urls)} مصادر ويب جاهزة للاستكشاف.")

                # Process URLs
                for url in urls:
                    if self._stop_requested:
                        self.stop_reason = "تم إيقاف عملية الزحف يدوياً بواسطة المستخدم"
                        logger.info("Stopping URL processing due to cancel signal")
                        break
                    if self.sources_collected >= self.cfg.crawler.max_sources:
                        self.stop_reason = f"تم الوصول إلى الحد الأقصى للمصادر المحدد ({self.cfg.crawler.max_sources} مصادر)"
                        self.add_log("success", f"تم اكتمال الزحف: تم الوصول إلى الحد الأقصى المطلوب ({self.cfg.crawler.max_sources} مصادر).")
                        break
                    if self._is_time_up():
                        self.stop_reason = f"تم انتهاء المهلة الزمنية المحددة للزحف ({self.cfg.crawler.time_limit_minutes} دقيقة)"
                        self.add_log("info", f"تم إنهاء الزحف: انتهت المهلة الزمنية المحددة ({self.cfg.crawler.time_limit_minutes} دقيقة).")
                        break
                    
                    self._process_url(url, topic)

                # Mark topic done
                update_topic_status(topic.id, "done")
                save_session_state(self.session_id, STATUS_RUNNING)

        except KeyboardInterrupt:
            logger.warning("\nOrchestrator interrupted by user (Ctrl+C).")
            raise
        except Exception as e:
            logger.exception(f"Orchestrator fatal error: {e}")
            self.stop_reason = f"حدث خطأ غير متوقع أثناء الزحف: {str(e)[:70]}"
            self.add_log("error", f"خطأ أثناء الزحف: {str(e)[:100]}")
            raise
        finally:
            self.is_finished = True
            if self._stop_requested:
                save_session_state(self.session_id, STATUS_PAUSED)
                if not self.stop_reason:
                    self.stop_reason = "تم إيقاف عملية الزحف بواسطة المستخدم"
                self.add_log("info", "تم إيقاف عملية الزحف مؤقتاً.")
            else:
                mark_session_complete(self.session_id)
                if not self.stop_reason:
                    self.stop_reason = f"اكتملت الجلسة بنجاح مع جمع {self.sources_collected} مصادر"
                self.add_log("success", f"انتهت الجلسة: {self.stop_reason}")

        logger.info(f"Orchestrator finished. Collected {self.sources_collected} sources. Reason: {self.stop_reason}")
