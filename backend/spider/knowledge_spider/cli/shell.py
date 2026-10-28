"""
Module: cli/shell.py
Purpose: Interactive REPL (Read-Eval-Print Loop) for exploring a crawled session.
         Allows users to inspect graph nodes, edges, and extracted sources
         without writing SQL queries.
Author: KnowledgeSpider Engine
"""

from __future__ import annotations

import cmd
from rich.console import Console
from rich.table import Table

from knowledge_spider.core.session import load_session
from knowledge_spider.knowledge.graph import KnowledgeGraphManager
from knowledge_spider.storage.database import get_topic_by_name, get_sources_by_topic

console = Console()


class KnowledgeShell(cmd.Cmd):
    intro = (
        "[bold cyan]Welcome to the KnowledgeSpider Interactive Shell.[/]\n"
        "Type [bold green]help[/] or [bold green]?[/] to list commands.\n"
        "Type [bold green]exit[/] to quit.\n"
    )
    prompt = "spider> "

    def __init__(self, session_id: str):
        super().__init__()
        # Strip rich formatting for the actual cmd prompt
        self.prompt = f"spider[{session_id[:8]}]> "
        self.session_id = session_id
        
        try:
            self.session = load_session(session_id)
            self.manager = KnowledgeGraphManager(session_id)
            self.graph = self.manager.build_graph()
        except Exception as e:
            console.print(f"[bold red]Failed to load session:[/] {e}")
            raise

    def do_summary(self, arg: str) -> None:
        """
        summary
        Print the high-level network summary and top central concepts.
        """
        summary = self.manager.get_graph_summary()
        console.print(f"\n[bold]Nodes:[/] {summary['total_nodes']}  |  [bold]Edges:[/] {summary['total_edges']}  |  [bold]Density:[/] {summary['graph_density']}")
        
        table = Table(title="Top Concepts")
        table.add_column("Rank")
        table.add_column("Topic")
        table.add_column("Centrality Score")
        
        for i, concept in enumerate(summary["top_concepts"], 1):
            table.add_row(str(i), concept["topic"], f"{concept['pagerank']:.4f}")
        console.print(table)
        console.print()

    def do_explore(self, arg: str) -> None:
        """
        explore <topic_name>
        Show immediate sub-topics (outgoing edges) connected to <topic_name>.
        """
        if not arg:
            console.print("[yellow]Usage: explore <topic_name>[/]")
            return

        topic_name = arg.strip()
        if topic_name not in self.graph:
            console.print(f"[yellow]Topic '{topic_name}' not found in the graph.[/]")
            return

        successors = list(self.graph.successors(topic_name))
        if not successors:
            console.print(f"No outgoing connections from [bold cyan]{topic_name}[/].")
            return

        table = Table(title=f"Sub-topics of '{topic_name}'")
        table.add_column("Topic")
        table.add_column("Edge Weight", justify="right")

        for succ in successors:
            edge_data = self.graph.get_edge_data(topic_name, succ)
            weight = edge_data.get("weight", 0.0) if edge_data else 0.0
            table.add_row(succ, f"{weight:.2f}")

        console.print(table)
        console.print()

    def do_sources(self, arg: str) -> None:
        """
        sources <topic_name>
        List the URLs and Quality Scores of the sources crawled for <topic_name>.
        """
        if not arg:
            console.print("[yellow]Usage: sources <topic_name>[/]")
            return

        topic_name = arg.strip()
        topic = get_topic_by_name(self.session_id, topic_name)
        if not topic:
            console.print(f"[yellow]Topic '{topic_name}' not found.[/]")
            return

        sources = get_sources_by_topic(topic.id)
        if not sources:
            console.print(f"No sources collected for [bold cyan]{topic_name}[/].")
            return

        table = Table(title=f"Sources for '{topic_name}'")
        table.add_column("Quality", justify="right")
        table.add_column("Domain", style="dim")
        table.add_column("URL", style="blue")

        for s in sources:
            table.add_row(f"{s.quality_score:.2f}", s.domain, s.url)

        console.print(table)
        console.print()

    def do_exit(self, arg: str) -> bool:
        """
        exit
        Exit the interactive shell.
        """
        console.print("Goodbye!")
        return True
    
    # Aliases
    do_quit = do_exit
    do_EOF = do_exit


def start_shell(session_id: str) -> None:
    """Launch the interactive REPL for the given session."""
    # We print the intro using rich, then let cmd handle the loop
    shell = KnowledgeShell(session_id)
    console.print(shell.intro)
    shell.intro = "" # Prevent cmd from printing unformatted intro
    shell.cmdloop()
