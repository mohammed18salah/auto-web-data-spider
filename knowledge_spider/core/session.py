"""
Module: core/session.py
Purpose: Session lifecycle manager — create new crawl sessions, load existing
         ones by UUID, save in-progress state, and list all sessions.
         Sessions persist across process restarts via SQLite, enabling
         pause-and-resume without losing crawl progress.
Author: KnowledgeSpider Engine
"""

from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from knowledge_spider.core.config import Config, get_config
from knowledge_spider.storage.database import (
    create_db_and_tables,
    create_session as db_create_session,
    get_session_by_id as db_get_session,
    list_sessions as db_list_sessions,
    update_session_status,
    get_session_stats,
)
from knowledge_spider.storage.models import SessionModel
from knowledge_spider.utils.logger import logger, setup_logger

# ── Public status constants ───────────────────────────────────────────────────
STATUS_RUNNING   = "running"
STATUS_PAUSED    = "paused"
STATUS_COMPLETE  = "complete"


# ── Session creation ──────────────────────────────────────────────────────────

def create_session(seed_topic: str, config: Optional[Config] = None) -> SessionModel:
    """
    Initialise the database, create a new session row, and set up logging.

    Args:
        seed_topic: The user-supplied root topic string (e.g. "DNS").
        config:     Config instance; uses global singleton if not supplied.

    Returns:
        The persisted SessionModel with a fresh UUID and status='running'.
    """
    cfg = config or get_config()
    create_db_and_tables()

    session_id = str(uuid.uuid4())
    setup_logger(session_id=session_id)

    session = SessionModel(
        id=session_id,
        seed_topic=seed_topic.strip(),
        status=STATUS_RUNNING,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        config_snapshot=cfg.to_json(),
    )

    persisted = db_create_session(session)
    logger.info(
        f"New session created | id={session_id[:8]}... "
        f"topic='{seed_topic}' depth={cfg.crawler.max_depth} "
        f"max_sources={cfg.crawler.max_sources}"
    )
    return persisted


# ── Session loading ───────────────────────────────────────────────────────────

def load_session(session_id: str) -> SessionModel:
    """
    Load an existing session from the database by its UUID.

    Args:
        session_id: Full UUID string of the session to load.

    Returns:
        The matching SessionModel.

    Raises:
        ValueError: If no session with that ID exists in the database.
    """
    create_db_and_tables()
    session = db_get_session(session_id)
    if session is None:
        raise ValueError(f"Session not found: {session_id}")

    setup_logger(session_id=session_id)
    logger.info(
        f"Session loaded | id={session_id[:8]}... "
        f"topic='{session.seed_topic}' status={session.status}"
    )
    return session


# ── State persistence ─────────────────────────────────────────────────────────

def save_session_state(session_id: str, status: str = STATUS_RUNNING) -> None:
    """
    Persist the current session status to SQLite.

    Called periodically during the crawl loop to support resume.
    After a clean Ctrl+C the status is set to STATUS_PAUSED so
    the orchestrator can pick up where it left off.

    Args:
        session_id: UUID of the session to update.
        status:     New status string — use module constants.
    """
    ok = update_session_status(session_id, status)
    if ok:
        logger.debug(f"Session {session_id[:8]}... state saved -> {status}")
    else:
        logger.warning(f"save_session_state: session {session_id} not found in DB")


def mark_session_complete(session_id: str) -> None:
    """
    Mark a session as complete (crawl finished all stopping conditions).

    Args:
        session_id: UUID of the session to mark.
    """
    save_session_state(session_id, STATUS_COMPLETE)
    logger.info(f"Session {session_id[:8]}... marked COMPLETE")


def pause_session(session_id: str) -> None:
    """
    Mark a session as paused (e.g. on KeyboardInterrupt).

    Args:
        session_id: UUID of the session to pause.
    """
    save_session_state(session_id, STATUS_PAUSED)
    logger.info(f"Session {session_id[:8]}... marked PAUSED — resume with --session-id")


# ── Session listing ───────────────────────────────────────────────────────────

def list_sessions() -> list[SessionModel]:
    """
    Return all sessions from the database, newest first.

    Returns:
        List of SessionModel rows ordered by created_at descending.
    """
    create_db_and_tables()
    sessions = db_list_sessions()
    logger.debug(f"list_sessions: found {len(sessions)} session(s)")
    return sessions


def get_session_summary(session_id: str) -> dict:
    """
    Build a human-readable summary dict for display or export.

    Combines session metadata with live aggregate stats from the DB.

    Args:
        session_id: UUID of the session to summarise.

    Returns:
        Dict with keys: id, seed_topic, status, created_at, stats (sub-dict).

    Raises:
        ValueError: If the session does not exist.
    """
    session = load_session(session_id)
    stats   = get_session_stats(session_id)

    return {
        "id":          session.id,
        "seed_topic":  session.seed_topic,
        "status":      session.status,
        "created_at":  session.created_at.isoformat(),
        "updated_at":  session.updated_at.isoformat(),
        "stats":       stats,
    }


# ── Resume guard ──────────────────────────────────────────────────────────────

def assert_resumable(session_id: str) -> SessionModel:
    """
    Load a session and verify it is in a resumable state (paused).

    Args:
        session_id: UUID of the session to resume.

    Returns:
        The loaded SessionModel.

    Raises:
        ValueError: If session doesn't exist or is not paused.
    """
    session = load_session(session_id)
    if session.status not in (STATUS_PAUSED, STATUS_RUNNING):
        raise ValueError(
            f"Session {session_id[:8]}... has status '{session.status}' "
            f"— only 'paused' or 'running' sessions can be resumed."
        )
    logger.info(f"Session {session_id[:8]}... is resumable (status={session.status})")
    return session
