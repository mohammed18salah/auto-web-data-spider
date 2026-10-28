"""
Module: export/exporter.py
Purpose: Translates SQLite session data into portable JSON or CSV files.
         Outputs nodes, edges, sources, and NLP terms for downstream consumption.
Author: KnowledgeSpider Engine
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from knowledge_spider.core.config import get_config
from knowledge_spider.core.session import get_session_summary
from knowledge_spider.storage.database import (
    get_topics_by_session,
    get_edges_by_session,
    get_sources_by_topic,
    get_sources_by_session,
    get_terms_by_topic,
)
from knowledge_spider.utils.logger import logger


class DataExporter:
    """Handles data serialisation to local file system formats."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.cfg = get_config()
        self.output_dir = Path(__file__).resolve().parent.parent.parent / self.cfg.export.output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _gather_payload(self) -> dict:
        """
        Extract all relevant session data into a unified dictionary structure.
        """
        summary = get_session_summary(self.session_id)
        topics = get_topics_by_session(self.session_id)
        edges = get_edges_by_session(self.session_id)

        all_sources = get_sources_by_session(self.session_id)
        payload = {
            "session": summary,
            "all_sources": [
                {
                    "url": s.url,
                    "domain": s.domain,
                    "title": s.title,
                    "summary": s.summary,
                    "quality_score": s.quality_score,
                    "word_count": s.word_count,
                    "crawled_at": s.crawled_at.isoformat() if s.crawled_at else None,
                }
                for s in all_sources
            ],
            "topics": [],
            "edges": [
                {
                    "source": edge.from_topic,
                    "target": edge.to_topic,
                    "weight": edge.weight,
                } for edge in edges
            ]
        }

        for topic in topics:
            sources = get_sources_by_topic(topic.id)
            terms = get_terms_by_topic(topic.id)
            
            topic_data = {
                "id": topic.id,
                "name": topic.name,
                "depth": topic.depth,
                "relevance_score": topic.relevance_score,
                "sources": [
                    {
                        "url": s.url,
                        "domain": s.domain,
                        "title": s.title,
                        "summary": s.summary,
                        "quality_score": s.quality_score,
                        "word_count": s.word_count
                    } for s in sources
                ],
                "top_terms": [
                    {
                        "term": t.term,
                        "frequency": t.frequency
                    } for t in terms[:20]  # Cap terms per topic in JSON to keep size reasonable
                ]
            }
            payload["topics"].append(topic_data)

        return payload

    def export_json(self) -> Path:
        """
        Export the session data as a structured JSON file.
        
        Returns:
            Path to the saved JSON file.
        """
        payload = self._gather_payload()
        
        filepath = self.output_dir / f"spider_{self.session_id[:8]}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Exported JSON to {filepath.resolve()}")
        return filepath

    def export_csv(self) -> Path:
        """
        Export the session's parsed sources to a flat CSV file.
        
        Returns:
            Path to the saved CSV file.
        """
        topics = get_topics_by_session(self.session_id)
        
        filepath = self.output_dir / f"spider_sources_{self.session_id[:8]}.csv"
        
        with open(filepath, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["topic_name", "depth", "domain", "url", "quality_score", "word_count", "summary"])
            
            count = 0
            for topic in topics:
                sources = get_sources_by_topic(topic.id)
                for s in sources:
                    writer.writerow([
                        topic.name,
                        topic.depth,
                        s.domain,
                        s.url,
                        round(s.quality_score, 3),
                        s.word_count,
                        s.summary.replace("\n", " ")
                    ])
                    count += 1
                    
        logger.info(f"Exported {count} sources to CSV at {filepath.resolve()}")
        return filepath
