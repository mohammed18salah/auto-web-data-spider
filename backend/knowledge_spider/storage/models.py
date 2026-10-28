"""
Module: storage/models.py
Purpose: SQLModel ORM data models for all KnowledgeSpider database tables.
         Defines Session, Topic, Source, TopicEdge, and Term with exact
         schema matching the project specification. No DB connection here —
         pure model definitions only.
Author: KnowledgeSpider Engine
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


# ── SessionModel ─────────────────────────────────────────────────────────────

class SessionModel(SQLModel, table=True):
    """
    Represents a single crawl session.

    Each run of KnowledgeSpider creates one session. Sessions can be paused
    and resumed; the config_snapshot preserves the exact settings used.
    """

    __tablename__ = "sessions"

    id: str = Field(primary_key=True, description="UUID v4 session identifier")
    seed_topic: str = Field(index=True, description="The initial topic provided by the user")
    status: str = Field(
        default="running",
        description="One of: running | paused | complete",
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    config_snapshot: str = Field(
        default="{}",
        description="JSON-serialised copy of config.toml used for this session",
    )


# ── TopicModel ────────────────────────────────────────────────────────────────

class TopicModel(SQLModel, table=True):
    """
    Represents a topic node in the knowledge graph.

    Topics are discovered either from user input (seed) or extracted from
    crawled pages. Each has a depth level and a relevance score relative
    to the seed topic.
    """

    __tablename__ = "topics"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(foreign_key="sessions.id", index=True)
    name: str = Field(index=True, description="Human-readable topic label")
    depth: int = Field(default=0, description="Crawl depth from seed (0 = seed)")
    relevance_score: float = Field(default=0.0, description="0.0–1.0 relevance to seed")
    status: str = Field(
        default="queued",
        description="One of: queued | processing | done | skipped",
    )
    is_seed: bool = Field(default=False, description="True only for the root seed topic")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ── SourceModel ───────────────────────────────────────────────────────────────

class SourceModel(SQLModel, table=True):
    """
    Represents a crawled web page (source document).

    Each source is uniquely identified by its content_hash so that identical
    content fetched from different URLs is never stored twice.
    """

    __tablename__ = "sources"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(foreign_key="sessions.id", index=True)
    topic_id: int = Field(foreign_key="topics.id", index=True)
    url: str = Field(description="Full URL of the crawled page")
    domain: str = Field(index=True, description="Registered domain extracted from URL")
    title: str = Field(default="", description="HTML <title> of the page")
    summary: str = Field(default="", description="Extractive summary (N sentences)")
    quality_score: float = Field(default=0.0, description="Composite quality score 0–1")
    depth_level: int = Field(default=0, description="Crawl depth at which this was fetched")
    content_hash: str = Field(
        index=True,
        description="SHA-256 of normalised page text — dedup key",
    )
    word_count: int = Field(default=0, description="Number of words in extracted text")
    crawled_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ── TopicEdgeModel ────────────────────────────────────────────────────────────

class TopicEdgeModel(SQLModel, table=True):
    """
    Represents a directed edge in the topic knowledge graph.

    An edge from_topic -> to_topic with a weight encodes how strongly
    the source topic implies or references the target topic.
    The (session_id, from_topic, to_topic) triple must be unique.
    """

    __tablename__ = "topic_edges"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(foreign_key="sessions.id", index=True)
    from_topic: str = Field(index=True, description="Source topic name")
    to_topic: str = Field(index=True, description="Target topic name")
    weight: float = Field(default=1.0, description="Edge strength 0–1")


# ── TermModel ─────────────────────────────────────────────────────────────────

class TermModel(SQLModel, table=True):
    """
    Represents a TF-IDF extracted term from a topic's collected sources.

    Multiple terms are stored per topic, ranked by their TF-IDF score.
    These power the knowledge graph's semantic labelling.
    """

    __tablename__ = "terms"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(foreign_key="sessions.id", index=True)
    topic_id: int = Field(foreign_key="topics.id", index=True)
    term: str = Field(index=True, description="Extracted keyword or key phrase")
    tfidf_score: float = Field(default=0.0, description="TF-IDF relevance score")
    frequency: int = Field(default=1, description="Raw term frequency across sources")


# ── Convenience re-exports ────────────────────────────────────────────────────
# Other modules import the cleaner alias names (without "Model" suffix)

Session = SessionModel
Topic = TopicModel
Source = SourceModel
TopicEdge = TopicEdgeModel
Term = TermModel
