"""
Module: cli/main.py
Purpose: Command Line Interface for the KnowledgeSpider Engine using Typer and Rich.
         Provides commands to start crawls, list sessions, and view graph summaries.
Author: KnowledgeSpider Engine
"""

from __future__ import annotations

import sys
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from knowledge_spider.core.config import get_config
from knowledge_spider.core.session import create_session, load_session, pause_session, STATUS_RUNNING
from knowledge_spider.storage.database import create_db_and_tables, list_sessions, get_session_stats
from knowledge_spider.crawler.orchestrator import CrawlerOrchestrator
from knowledge_spider.knowledge.graph import KnowledgeGraphManager
from knowledge_spider.utils.logger import set_log_level

app = typer.Typer(help="KnowledgeSpider: Autonomous Web Crawling & Knowledge Graph Engine")
console = Console()


@app.callback()
def main_callback(debug: bool = False):
    """Global options."""
    if debug:
        set_log_level("DEBUG")
    # Ensure DB is ready before any command
    create_db_and_tables()


@app.command()
def start(
    topic: str = typer.Argument(..., help="The root seed topic to begin crawling"),
    max_depth: int = typer.Option(None, help="Override config.toml max_depth"),
    max_sources: int = typer.Option(None, help="Override config.toml max_sources"),
):
    """Start a fresh autonomous crawl session."""
    cfg = get_config()
    if max_depth is not None:
        cfg.crawler.max_depth = max_depth
    if max_sources is not None:
        cfg.crawler.max_sources = max_sources

    session = create_session(topic, cfg)
    console.print(Panel(f"Starting new session: [bold cyan]{session.id}[/]\nSeed Topic: [bold green]{topic}[/]", title="KnowledgeSpider"))

    orchestrator = CrawlerOrchestrator(session.id, cfg)
    try:
        orchestrator.run()
        console.print("[bold green]Crawl completed successfully![/]")
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Crawl interrupted by user. Pausing session...[/]")
        pause_session(session.id)
        sys.exit(0)
    except Exception as e:
        console.print(f"[bold red]Fatal error during crawl:[/] {e}")
        pause_session(session.id)
        sys.exit(1)


@app.command()
def resume(session_id: str = typer.Argument(..., help="UUID of the paused session")):
    """Resume a previously paused or interrupted crawl session."""
    session = load_session(session_id)
    if not session:
        console.print(f"[bold red]Error:[/] Session {session_id} not found.")
        raise typer.Exit(code=1)

    if session.status == "complete":
        console.print("[bold yellow]This session is already complete.[/]")
        raise typer.Exit(code=0)

    console.print(Panel(f"Resuming session: [bold cyan]{session.id}[/]\nSeed Topic: [bold green]{session.seed_topic}[/]", title="KnowledgeSpider"))
    
    # We use the global config here, but a production grade system might load the snapshot
    cfg = get_config()
    orchestrator = CrawlerOrchestrator(session.id, cfg)
    try:
        orchestrator.run()
        console.print("[bold green]Crawl completed successfully![/]")
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Crawl interrupted by user. Pausing session...[/]")
        pause_session(session.id)
        sys.exit(0)


@app.command()
def sessions():
    """List all recorded crawl sessions and their statistics."""
    sessions_list = list_sessions()
    if not sessions_list:
        console.print("[yellow]No sessions found in database.[/]")
        return

    table = Table(title="KnowledgeSpider Sessions")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Seed Topic", style="green")
    table.add_column("Status")
    table.add_column("Created", style="dim")
    table.add_column("Sources")

    for s in sessions_list:
        stats = get_session_stats(s.id)
        status_color = "green" if s.status == "complete" else "yellow" if s.status == "paused" else "blue"
        table.add_row(
            s.id[:8] + "...",
            s.seed_topic,
            f"[{status_color}]{s.status}[/]",
            s.created_at.strftime("%Y-%m-%d %H:%M"),
            str(stats["sources_total"])
        )

    console.print(table)


@app.command()
def graph(session_id: str = typer.Argument(..., help="UUID of the session to analyze")):
    """Compute and display the PageRank Knowledge Graph summary for a session."""
    session = load_session(session_id)
    if not session:
        console.print(f"[bold red]Error:[/] Session {session_id} not found.")
        raise typer.Exit(code=1)

    console.print(f"Building graph for [cyan]{session.seed_topic}[/]...")
    
    manager = KnowledgeGraphManager(session_id)
    summary = manager.get_graph_summary()
    
    if summary["total_nodes"] == 0:
        console.print("[yellow]Graph is empty. Run a crawl first.[/]")
        return

    console.print(f"\n[bold]Graph Statistics:[/]")
    console.print(f"  Nodes (Topics): {summary['total_nodes']}")
    console.print(f"  Edges (Links):  {summary['total_edges']}")
    console.print(f"  Density:        {summary['graph_density']}")

    console.print("\n[bold]Top Central Concepts (PageRank):[/]")
    table = Table()
    table.add_column("Rank", justify="right", style="dim")
    table.add_column("Topic", style="magenta")
    table.add_column("Centrality Score", justify="right", style="green")

    for i, concept in enumerate(summary["top_concepts"], 1):
        table.add_row(str(i), concept["topic"], f"{concept['pagerank']:.4f}")
    
    console.print(table)


if __name__ == "__main__":
    app()
