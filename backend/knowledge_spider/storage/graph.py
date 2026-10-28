"""
Module: storage/graph.py
Purpose: NetworkX-backed knowledge graph storage and analysis interface.
         Bridges SQLite persistence and in-memory graph models.
Author: KnowledgeSpider Engine
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Dict, Any
import networkx as nx

from knowledge_spider.knowledge.graph import KnowledgeGraphManager
from knowledge_spider.storage.database import (
    get_edges_by_session,
    get_topics_by_session,
)
from knowledge_spider.utils.logger import logger


def load_session_graph(session_id: str) -> nx.DiGraph:
    """
    Construct and return a NetworkX DiGraph for the specified session.

    Args:
        session_id: Target session UUID.

    Returns:
        Populated nx.DiGraph instance.
    """
    manager = KnowledgeGraphManager(session_id)
    return manager.build_graph()


def get_graph_summary(session_id: str) -> Dict[str, Any]:
    """
    Compute graph metrics, top central concepts, and node/edge statistics.

    Args:
        session_id: Target session UUID.

    Returns:
        Dictionary with total_nodes, total_edges, top_concepts, and density.
    """
    manager = KnowledgeGraphManager(session_id)
    return manager.get_graph_summary()


def export_graph_to_gexf(session_id: str, output_path: Path | str) -> Path:
    """
    Export the session's knowledge graph to GEXF format for Gephi/visualizer tools.

    Args:
        session_id: Target session UUID.
        output_path: File destination path.

    Returns:
        Path to the written GEXF file.
    """
    graph = load_session_graph(session_id)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    nx.write_gexf(graph, str(path))
    logger.info(f"Graph exported to GEXF at {path.resolve()}")
    return path


__all__ = [
    "KnowledgeGraphManager",
    "load_session_graph",
    "get_graph_summary",
    "export_graph_to_gexf",
]
