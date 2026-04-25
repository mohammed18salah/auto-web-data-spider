"""
Module: knowledge/graph.py
Purpose: NetworkX-based knowledge graph generation and analysis.
         Reads Topics and TopicEdges from the SQLite database to build
         a directed graph. Computes PageRank and Centrality to identify
         the most crucial nodes in the discovered knowledge domain.
Author: KnowledgeSpider Engine
"""

from __future__ import annotations

import networkx as nx

from knowledge_spider.storage.database import (
    get_edges_by_session,
    get_topics_by_session,
    get_session_stats,
)
from knowledge_spider.utils.logger import logger


class KnowledgeGraphManager:
    """
    Builds and analyses a directed graph from session data.
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.graph = nx.DiGraph()

    def build_graph(self) -> nx.DiGraph:
        """
        Query the database and populate the NetworkX DiGraph.

        Nodes: Topics (with their depth and relevance score as attributes).
        Edges: Directed links from parent topics to discovered subtopics (with weight).

        Returns:
            The populated nx.DiGraph.
        """
        self.graph.clear()

        # Load topics (nodes)
        topics = get_topics_by_session(self.session_id)
        topic_map = {}  # Map ID -> Name for easy edge resolution

        for topic in topics:
            topic_map[topic.id] = topic.name
            self.graph.add_node(
                topic.name,
                depth=topic.depth,
                relevance=topic.relevance_score,
                status=topic.status,
            )

        # Load edges
        edges = get_edges_by_session(self.session_id)
        for edge in edges:
            if edge.from_topic and edge.to_topic:
                self.graph.add_edge(edge.from_topic, edge.to_topic, weight=edge.weight)

        logger.debug(
            f"Knowledge Graph built: {self.graph.number_of_nodes()} nodes, "
            f"{self.graph.number_of_edges()} edges."
        )
        return self.graph

    def get_central_topics(self, top_n: int = 5) -> list[tuple[str, float]]:
        """
        Calculate PageRank to find the most 'central' or 'authoritative' 
        topics in the knowledge structure.

        Args:
            top_n: Number of top results to return.

        Returns:
            List of tuples: (topic_name, pagerank_score), sorted descending.
        """
        if self.graph.number_of_nodes() == 0:
            return []

        # Calculate PageRank
        # We use weight='weight' if available, otherwise fallback to unweighted
        try:
            pagerank = nx.pagerank(self.graph, weight="weight")
        except Exception as e:
            logger.warning(f"PageRank computation failed (perhaps graph is empty): {e}")
            return []

        # Sort descending by score
        sorted_nodes = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)
        return sorted_nodes[:top_n]

    def get_graph_summary(self) -> dict:
        """
        Return a high-level statistical summary of the knowledge graph.

        Returns:
            A dictionary containing node count, edge count, density, and top concepts.
        """
        if self.graph.number_of_nodes() == 0:
            self.build_graph()

        nodes = self.graph.number_of_nodes()
        edges = self.graph.number_of_edges()
        
        # Density: Ratio of actual edges to possible edges
        density = nx.density(self.graph) if nodes > 1 else 0.0

        top_concepts = self.get_central_topics(top_n=3)

        return {
            "session_id": self.session_id,
            "total_nodes": nodes,
            "total_edges": edges,
            "graph_density": round(density, 4),
            "top_concepts": [
                {"topic": name, "pagerank": round(score, 4)}
                for name, score in top_concepts
            ],
        }
