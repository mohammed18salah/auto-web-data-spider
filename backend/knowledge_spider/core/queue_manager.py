"""
Module: core/queue_manager.py
Purpose: Priority-based topic queue with visited-set deduplication.
         Manages queued topics prioritizing shallower depth and higher relevance.
Author: KnowledgeSpider Engine
"""

from __future__ import annotations

import heapq
from threading import Lock
from typing import Optional, List, Set, Any
from dataclasses import dataclass, field

from knowledge_spider.storage.models import TopicModel
from knowledge_spider.storage.database import get_topics_by_session
from knowledge_spider.utils.logger import logger


@dataclass(order=True)
class PrioritizedTopic:
    """Wrapper to prioritize topics in a heap: lowest depth first, highest relevance first."""
    depth: int
    neg_relevance: float
    topic_name: str = field(compare=False)
    topic_data: Optional[TopicModel] = field(default=None, compare=False)


class TopicQueueManager:
    """
    Thread-safe Priority Queue for crawl topics.

    Features:
    - Orders by: depth ascending (shallower first), then relevance score descending.
    - Set-based deduplication to prevent revisiting the same topic multiple times.
    - Optional synchronization with SQLite session state.
    """

    def __init__(self, session_id: Optional[str] = None, max_depth: int = 3):
        self.session_id = session_id
        self.max_depth = max_depth
        self._heap: List[PrioritizedTopic] = []
        self._visited: Set[str] = set()
        self._enqueued: Set[str] = set()
        self._lock = Lock()

    def _normalize(self, topic: str) -> str:
        """Normalize topic string for deduplication."""
        return topic.strip().lower()

    def push(self, topic: TopicModel) -> bool:
        """
        Add a topic to the priority queue if within max_depth and not previously visited/queued.

        Returns:
            True if added, False if duplicate or exceeds max_depth.
        """
        if topic.depth > self.max_depth:
            logger.debug(f"Queue: Skipped '{topic.name}' (depth {topic.depth} > {self.max_depth})")
            return False

        norm = self._normalize(topic.name)
        with self._lock:
            if norm in self._visited or norm in self._enqueued:
                return False

            self._enqueued.add(norm)
            # Min-heap ordered by (depth ASC, -relevance ASC)
            item = PrioritizedTopic(
                depth=topic.depth,
                neg_relevance=-float(topic.relevance_score),
                topic_name=topic.name,
                topic_data=topic,
            )
            heapq.heappush(self._heap, item)
            return True

    def pop(self) -> Optional[TopicModel]:
        """
        Remove and return the highest priority topic from the queue.

        Returns:
            TopicModel or None if empty.
        """
        with self._lock:
            while self._heap:
                item = heapq.heappop(self._heap)
                norm = self._normalize(item.topic_name)
                self._enqueued.discard(norm)
                self._visited.add(norm)
                return item.topic_data
            return None

    def peek(self) -> Optional[TopicModel]:
        """View the top item without removing it."""
        with self._lock:
            if self._heap:
                return self._heap[0].topic_data
            return None

    def mark_visited(self, topic_name: str) -> None:
        """Mark a topic as visited without having to pop it."""
        with self._lock:
            self._visited.add(self._normalize(topic_name))

    def is_visited(self, topic_name: str) -> bool:
        """Check if a topic has been visited."""
        with self._lock:
            return self._normalize(topic_name) in self._visited

    def load_from_session(self, session_id: str) -> int:
        """
        Populate the queue from persistent database state for resume support.

        Returns:
            Count of newly enqueued topics.
        """
        self.session_id = session_id
        topics = get_topics_by_session(session_id)
        count = 0
        for t in topics:
            if t.status in ("done", "skipped", "processing"):
                self.mark_visited(t.name)
            elif t.status == "queued":
                if self.push(t):
                    count += 1
        logger.info(f"Loaded {count} queued topics for session {session_id[:8]}")
        return count

    def size(self) -> int:
        """Number of items currently queued."""
        with self._lock:
            return len(self._heap)

    def is_empty(self) -> bool:
        """Return True if queue is empty."""
        with self._lock:
            return len(self._heap) == 0

    def clear(self) -> None:
        """Reset the queue and tracking sets."""
        with self._lock:
            self._heap.clear()
            self._visited.clear()
            self._enqueued.clear()
