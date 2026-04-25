"""
Module: storage/database.py
Purpose: SQLite engine setup via SQLModel and all CRUD operations for
         Session, Topic, Source, TopicEdge, and Term tables.
         Provides a single get_engine() factory and a clean CRUD API
         used by every other module that touches persistent storage.
Author: KnowledgeSpider Engine
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlmodel import Session as DBSession, SQLModel, create_engine, select, col

from knowledge_spider.storage.models import (
    SessionModel,
    SourceModel,
    TermModel,
    TopicEdgeModel,
    TopicModel,
)
from knowledge_spider.utils.logger import logger

# ── Engine ────────────────────────────────────────────────────────────────────

_DB_PATH: Path = Path("./knowledge_spider.db")
_engine = None  # lazy singleton


def get_engine(db_path: Path = _DB_PATH):
    """
    Return (and lazily create) the shared SQLite engine.

    Args:
        db_path: Path to the SQLite file. Defaults to ./knowledge_spider.db

    Returns:
        A SQLModel/SQLAlchemy engine bound to the given file.
    """
    global _engine
    if _engine is None:
        url = f"sqlite:///{db_path.resolve()}"
        _engine = create_engine(url, echo=False, connect_args={"check_same_thread": False})
        logger.debug(f"SQLite engine created at {db_path.resolve()}")
    return _engine


def create_db_and_tables(db_path: Path = _DB_PATH) -> None:
    """
    Create all tables defined in SQLModel metadata (idempotent).

    Args:
        db_path: Path to the SQLite file.
    """
    engine = get_engine(db_path)
    SQLModel.metadata.create_all(engine)
    logger.info(f"Database tables ensured at {db_path.resolve()}")


# ── Session CRUD ──────────────────────────────────────────────────────────────

def create_session(session: SessionModel) -> SessionModel:
    """
    Persist a new SessionModel row and return it.

    Args:
        session: A fully-constructed SessionModel instance.

    Returns:
        The persisted SessionModel (with any DB-generated defaults).
    """
    with DBSession(get_engine()) as db:
        db.add(session)
        db.commit()
        db.refresh(session)
        logger.debug(f"Session created: {session.id} (topic={session.seed_topic})")
        return session


def get_session_by_id(session_id: str) -> Optional[SessionModel]:
    """
    Fetch a SessionModel by its UUID primary key.

    Args:
        session_id: The UUID string of the session.

    Returns:
        SessionModel if found, None otherwise.
    """
    with DBSession(get_engine()) as db:
        return db.get(SessionModel, session_id)


def update_session_status(session_id: str, status: str) -> bool:
    """
    Update a session's status and refresh its updated_at timestamp.

    Args:
        session_id: Target session UUID.
        status: New status string (running | paused | complete).

    Returns:
        True if updated, False if session not found.
    """
    with DBSession(get_engine()) as db:
        row = db.get(SessionModel, session_id)
        if row is None:
            logger.warning(f"update_session_status: session {session_id} not found")
            return False
        row.status = status
        row.updated_at = datetime.utcnow()
        db.add(row)
        db.commit()
        logger.debug(f"Session {session_id} status -> {status}")
        return True


def list_sessions() -> list[SessionModel]:
    """
    Return all sessions ordered by creation time descending.

    Returns:
        List of SessionModel rows.
    """
    with DBSession(get_engine()) as db:
        stmt = select(SessionModel).order_by(col(SessionModel.created_at).desc())
        return db.exec(stmt).all()


# ── Topic CRUD ────────────────────────────────────────────────────────────────

def create_topic(topic: TopicModel) -> TopicModel:
    """
    Persist a new TopicModel row and return it.

    Args:
        topic: A fully-constructed TopicModel instance.

    Returns:
        The persisted TopicModel (id populated).
    """
    with DBSession(get_engine()) as db:
        db.add(topic)
        db.commit()
        db.refresh(topic)
        logger.debug(f"Topic created: '{topic.name}' depth={topic.depth}")
        return topic


def get_topic_by_name(session_id: str, name: str) -> Optional[TopicModel]:
    """
    Fetch a topic by session + name (case-sensitive).

    Args:
        session_id: The owning session UUID.
        name: The topic name to look up.

    Returns:
        TopicModel if found, None otherwise.
    """
    with DBSession(get_engine()) as db:
        stmt = (
            select(TopicModel)
            .where(TopicModel.session_id == session_id)
            .where(TopicModel.name == name)
        )
        return db.exec(stmt).first()


def update_topic_status(topic_id: int, status: str) -> bool:
    """
    Update a topic's processing status.

    Args:
        topic_id: Primary key of the topic row.
        status: New status (queued | processing | done | skipped).

    Returns:
        True if updated, False if not found.
    """
    with DBSession(get_engine()) as db:
        row = db.get(TopicModel, topic_id)
        if row is None:
            logger.warning(f"update_topic_status: topic {topic_id} not found")
            return False
        row.status = status
        db.add(row)
        db.commit()
        return True


def get_topics_by_session(session_id: str) -> list[TopicModel]:
    """
    Return all topics for a session ordered by depth then relevance.

    Args:
        session_id: The owning session UUID.

    Returns:
        List of TopicModel rows.
    """
    with DBSession(get_engine()) as db:
        stmt = (
            select(TopicModel)
            .where(TopicModel.session_id == session_id)
            .order_by(col(TopicModel.depth), col(TopicModel.relevance_score).desc())
        )
        return db.exec(stmt).all()


# ── Source CRUD ───────────────────────────────────────────────────────────────

def source_exists(content_hash: str) -> bool:
    """
    Check if a source with the given content hash already exists.

    Used as the deduplication gate before processing a fetched page.

    Args:
        content_hash: SHA-256 hex digest of the page text.

    Returns:
        True if a matching row exists.
    """
    with DBSession(get_engine()) as db:
        stmt = select(SourceModel).where(SourceModel.content_hash == content_hash)
        return db.exec(stmt).first() is not None


def create_source(source: SourceModel) -> Optional[SourceModel]:
    """
    Persist a new SourceModel. Skips silently if hash already exists.

    Args:
        source: A fully-constructed SourceModel instance.

    Returns:
        The persisted SourceModel, or None if it was a duplicate.
    """
    if source_exists(source.content_hash):
        logger.debug(f"Duplicate content skipped: {source.url}")
        return None
    with DBSession(get_engine()) as db:
        db.add(source)
        db.commit()
        db.refresh(source)
        logger.debug(f"Source saved: {source.url} (score={source.quality_score:.2f})")
        return source


def source_url_exists(url: str) -> bool:
    """
    Check if a source with the given URL already exists.
    
    Args:
        url: The absolute URL string.
        
    Returns:
        True if a matching row exists.
    """
    with DBSession(get_engine()) as db:
        stmt = select(SourceModel).where(SourceModel.url == url)
        return db.exec(stmt).first() is not None


def get_sources_by_topic(topic_id: int) -> list[SourceModel]:
    """
    Return all sources collected for a given topic.

    Args:
        topic_id: Primary key of the parent topic.

    Returns:
        List of SourceModel rows ordered by quality score descending.
    """
    with DBSession(get_engine()) as db:
        stmt = (
            select(SourceModel)
            .where(SourceModel.topic_id == topic_id)
            .order_by(col(SourceModel.quality_score).desc())
        )
        return db.exec(stmt).all()


# ── TopicEdge CRUD ────────────────────────────────────────────────────────────

def create_edge(edge: TopicEdgeModel) -> Optional[TopicEdgeModel]:
    """
    Persist a directed topic edge, ignoring duplicates silently.

    The (session_id, from_topic, to_topic) triple must be unique;
    if it already exists the function returns None.

    Args:
        edge: A fully-constructed TopicEdgeModel instance.

    Returns:
        The persisted edge, or None if it was a duplicate.
    """
    with DBSession(get_engine()) as db:
        existing = db.exec(
            select(TopicEdgeModel)
            .where(TopicEdgeModel.session_id == edge.session_id)
            .where(TopicEdgeModel.from_topic == edge.from_topic)
            .where(TopicEdgeModel.to_topic == edge.to_topic)
        ).first()
        if existing:
            return None
        db.add(edge)
        db.commit()
        db.refresh(edge)
        logger.debug(f"Edge: {edge.from_topic} -> {edge.to_topic} (w={edge.weight:.2f})")
        return edge


def get_edges_by_session(session_id: str) -> list[TopicEdgeModel]:
    """
    Return all topic edges for a session.

    Args:
        session_id: The owning session UUID.

    Returns:
        List of TopicEdgeModel rows.
    """
    with DBSession(get_engine()) as db:
        stmt = select(TopicEdgeModel).where(TopicEdgeModel.session_id == session_id)
        return db.exec(stmt).all()


# ── Term CRUD ─────────────────────────────────────────────────────────────────

def bulk_insert_terms(terms: list[TermModel]) -> int:
    """
    Insert multiple TermModel rows in a single transaction.

    Args:
        terms: List of TermModel instances to persist.

    Returns:
        Number of rows actually inserted.
    """
    if not terms:
        return 0
    with DBSession(get_engine()) as db:
        for term in terms:
            db.add(term)
        db.commit()
        logger.debug(f"Bulk inserted {len(terms)} terms for topic_id={terms[0].topic_id}")
        return len(terms)


def get_terms_by_topic(topic_id: int) -> list[TermModel]:
    """
    Return all terms for a topic ordered by TF-IDF score descending.

    Args:
        topic_id: Primary key of the parent topic.

    Returns:
        List of TermModel rows.
    """
    with DBSession(get_engine()) as db:
        stmt = (
            select(TermModel)
            .where(TermModel.topic_id == topic_id)
            .order_by(col(TermModel.tfidf_score).desc())
        )
        return db.exec(stmt).all()


# ── Stats helpers ─────────────────────────────────────────────────────────────

def get_session_stats(session_id: str) -> dict:
    """
    Return aggregate counts for a session (topics, sources, edges, terms).

    Args:
        session_id: The owning session UUID.

    Returns:
        Dict with keys: topics, sources_total, edges, terms,
        topics_done, topics_queued, avg_quality.
    """
    with DBSession(get_engine()) as db:
        topics   = db.exec(select(TopicModel).where(TopicModel.session_id == session_id)).all()
        sources  = db.exec(select(SourceModel).where(SourceModel.session_id == session_id)).all()
        edges    = db.exec(select(TopicEdgeModel).where(TopicEdgeModel.session_id == session_id)).all()
        terms    = db.exec(select(TermModel).where(TermModel.session_id == session_id)).all()

        done    = sum(1 for t in topics if t.status == "done")
        queued  = sum(1 for t in topics if t.status == "queued")
        avg_q   = round(sum(s.quality_score for s in sources) / len(sources), 3) if sources else 0.0

        return {
            "topics":        len(topics),
            "sources_total": len(sources),
            "edges":         len(edges),
            "terms":         len(terms),
            "topics_done":   done,
            "topics_queued": queued,
            "avg_quality":   avg_q,
        }
