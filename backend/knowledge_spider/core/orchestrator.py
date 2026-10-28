"""
Module: core/orchestrator.py
Purpose: Main orchestrator controller and pipeline coordinator.
         Wires all crawler, NLP, graph, and storage subsystems together.
Author: KnowledgeSpider Engine
"""

from __future__ import annotations

from typing import Optional, Dict
from threading import Lock

from knowledge_spider.core.config import Config, get_config
from knowledge_spider.crawler.orchestrator import CrawlerOrchestrator
from knowledge_spider.utils.logger import logger

# Thread-safe global registry for active running orchestrators
_active_orchestrators: Dict[str, CrawlerOrchestrator] = {}
_registry_lock = Lock()


def register_orchestrator(session_id: str, orchestrator: CrawlerOrchestrator) -> None:
    """Register an orchestrator as actively running."""
    with _registry_lock:
        _active_orchestrators[session_id] = orchestrator
        logger.debug(f"Registered active orchestrator for session {session_id[:8]}")


def unregister_orchestrator(session_id: str) -> Optional[CrawlerOrchestrator]:
    """Unregister an orchestrator when finished or cancelled."""
    with _registry_lock:
        orch = _active_orchestrators.pop(session_id, None)
        if orch:
            logger.debug(f"Unregistered active orchestrator for session {session_id[:8]}")
        return orch


def get_active_orchestrator(session_id: str) -> Optional[CrawlerOrchestrator]:
    """Retrieve an active orchestrator instance by session ID."""
    with _registry_lock:
        return _active_orchestrators.get(session_id)


def stop_orchestrator(session_id: str) -> bool:
    """
    Signal an active crawl orchestrator to gracefully stop.

    Returns:
        True if the orchestrator was found and stopped, False otherwise.
    """
    orch = get_active_orchestrator(session_id)
    if orch:
        orch.stop()
        logger.info(f"Sent stop signal to orchestrator for session {session_id[:8]}")
        return True
    return False


def stop_all_orchestrators() -> int:
    """
    Signal all running orchestrators to halt.

    Returns:
        Number of stopped orchestrators.
    """
    with _registry_lock:
        count = len(_active_orchestrators)
        for s_id, orch in _active_orchestrators.items():
            orch.stop()
            logger.info(f"Stopping session {s_id[:8]}")
        return count


# Orchestrator alias for backwards compatibility
Orchestrator = CrawlerOrchestrator

__all__ = [
    "CrawlerOrchestrator",
    "Orchestrator",
    "register_orchestrator",
    "unregister_orchestrator",
    "get_active_orchestrator",
    "stop_orchestrator",
    "stop_all_orchestrators",
]
