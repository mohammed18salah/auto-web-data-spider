"""
knowledge_spider/__init__.py

Public API for the KnowledgeSpider package.
"""
from knowledge_spider.core.config import get_config, load_config, reset_config, Config
from knowledge_spider.core.session import (
    create_session,
    load_session,
    list_sessions,
    pause_session,
    mark_session_complete,
    get_session_summary,
)
from knowledge_spider.crawler.orchestrator import CrawlerOrchestrator
from knowledge_spider.knowledge.graph import KnowledgeGraphManager
from knowledge_spider.export.exporter import DataExporter

__version__ = "1.0.0"
__author__ = "KnowledgeSpider Engine"

__all__ = [
    "get_config",
    "load_config",
    "reset_config",
    "Config",
    "create_session",
    "load_session",
    "list_sessions",
    "pause_session",
    "mark_session_complete",
    "get_session_summary",
    "CrawlerOrchestrator",
    "KnowledgeGraphManager",
    "DataExporter",
]
