import os
import sys
import json
import logging
from pathlib import Path
from threading import Lock
from typing import Optional, Dict, Any

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ensure backend root is on sys.path for clean, standard package imports
backend_dir = str(Path(__file__).resolve().parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from knowledge_spider.core.config import get_config, get_session_config, update_config, reload_config
from knowledge_spider.core.session import create_session
from knowledge_spider.storage.database import (
    create_db_and_tables,
    get_session_stats,
    list_sessions,
    update_session_status,
    delete_session,
)
from knowledge_spider.crawler.orchestrator import CrawlerOrchestrator
from knowledge_spider.knowledge.graph import KnowledgeGraphManager
from knowledge_spider.export.exporter import DataExporter
from knowledge_spider.utils.logger import setup_logger

# Setup Database and Logger on startup
create_db_and_tables()
setup_logger("api_backend")

app = FastAPI(
    title="Auto Web Data Spider API",
    description="Secure REST API backend for Auto Web Data Spider autonomous engine and desktop interface",
    version="1.0.0",
)

# ── CORS Security ─────────────────────────────────────────────────────────────
# Strict origin list to prevent arbitrary websites from communicating with the local API.
DEFAULT_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Allow custom origins via environment variable (e.g. for Docker or remote deployment)
env_origins = os.getenv("KNOWLEDGE_SPIDER_CORS_ORIGINS")
allowed_origins = list(DEFAULT_ORIGINS)
if env_origins:
    allowed_origins.extend([origin.strip() for origin in env_origins.split(",") if origin.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ── Active Crawlers Registry for Graceful Shutdown ─────────────────────────────
active_crawlers: Dict[str, CrawlerOrchestrator] = {}
crawler_lock = Lock()


class CrawlRequest(BaseModel):
    topic: str
    max_depth: int = 1
    max_sources: int = 5


class ConfigUpdateRequest(BaseModel):
    settings: Dict[str, Any]


def background_crawl_task(session_id: str, cfg):
    """Runs the crawler in the background while registering it for graceful stop control."""
    try:
        logging.info(f"Starting background crawl for session: {session_id}")
        orchestrator = CrawlerOrchestrator(session_id, cfg)
        with crawler_lock:
            active_crawlers[session_id] = orchestrator

        orchestrator.run()
        logging.info(f"Background crawl finished for session: {session_id}")
    except Exception as e:
        logging.error(f"Error in background crawl for session {session_id}: {e}")
    finally:
        with crawler_lock:
            active_crawlers.pop(session_id, None)


@app.get("/")
def read_root():
    return {"status": "ok", "message": "KnowledgeSpider API is running!", "version": "1.0.0"}


@app.post("/api/crawl")
def start_crawl(req: CrawlRequest, background_tasks: BackgroundTasks):
    """Starts a new crawl session with an isolated configuration copy."""
    # Use isolated session config so per-request parameters do NOT mutate the global singleton
    cfg = get_session_config({
        "crawler": {
            "max_depth": req.max_depth,
            "max_sources": req.max_sources,
        }
    })

    # Create the session in the DB
    session = create_session(req.topic, cfg)

    # Start the crawl process in the background
    background_tasks.add_task(background_crawl_task, session.id, cfg)

    return {
        "status": "started",
        "session_id": session.id,
        "topic": req.topic,
        "message": "Crawl started in the background."
    }


@app.post("/api/crawl/stop")
@app.post("/api/crawl/{session_id}/stop")
def stop_crawl(session_id: Optional[str] = None):
    """
    Gracefully stops an active crawl session.
    If no session_id is provided, stops all currently active crawls.
    """
    with crawler_lock:
        if session_id:
            orch = active_crawlers.get(session_id)
            if orch:
                orch.stop()
                return {"status": "stopping", "session_id": session_id, "message": "Stop signal sent to crawler."}
            else:
                update_session_status(session_id, "paused")
                return {"status": "stopped", "session_id": session_id, "message": "Session marked as stopped."}
        else:
            stopped = []
            for s_id, orch in list(active_crawlers.items()):
                orch.stop()
                stopped.append(s_id)
            return {"status": "stopping", "stopped_sessions": stopped, "message": f"Stop signal sent to {len(stopped)} crawler(s)."}


@app.get("/api/session/{session_id}")
def get_session_info(session_id: str):
    """Returns the stats (sources, topics, terms) for a session."""
    stats = get_session_stats(session_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Session not found or no stats available yet.")
    return stats


@app.delete("/api/session/{session_id}")
def delete_session_endpoint(session_id: str):
    """Deletes a session and its associated data from the database."""
    with crawler_lock:
        orch = active_crawlers.get(session_id)
        if orch:
            orch.stop()

    success = delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found.")
    return {"status": "deleted", "session_id": session_id}


@app.get("/api/graph/{session_id}")
def get_graph(session_id: str):
    """Returns the knowledge graph summary (nodes, edges, top concepts)."""
    try:
        manager = KnowledgeGraphManager(session_id)
        summary = manager.get_graph_summary()
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/export/{session_id}")
def export_session_data(session_id: str):
    """Generates the JSON export and returns the content directly."""
    try:
        exporter = DataExporter(session_id)
        json_path = exporter.export_json()

        if not json_path or not json_path.exists():
            raise HTTPException(status_code=404, detail="Export failed or file not found.")

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions")
def get_all_sessions():
    """Returns a list of all historical sessions."""
    try:
        sessions = list_sessions()
        result = []
        for s in sessions:
            stats = get_session_stats(s.id)
            result.append({
                "id": s.id,
                "topic": s.seed_topic,
                "status": s.status,
                "sources_analyzed": stats["sources_total"] if stats else 0,
                "created_at": s.created_at.isoformat() if s.created_at else None
            })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/config")
def get_config_endpoint():
    """Returns the current runtime configuration."""
    cfg = get_config()
    return json.loads(cfg.to_json())


@app.post("/api/config")
def update_config_endpoint(req: ConfigUpdateRequest):
    """Updates runtime configuration safely."""
    try:
        updated = update_config(req.settings)
        return {"status": "updated", "config": json.loads(updated.to_json())}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    # Run the server locally on port 8000
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
