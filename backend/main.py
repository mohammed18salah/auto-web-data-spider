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
    get_sources_by_session,
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
completed_crawlers: Dict[str, dict] = {}
crawler_lock = Lock()


class CrawlRequest(BaseModel):
    topic: str
    max_depth: int = 1
    max_sources: int = 5
    lang: Optional[str] = "en"


class ConfigUpdateRequest(BaseModel):
    settings: Dict[str, Any]


def background_crawl_task(session_id: str, cfg, lang: str = "en"):
    """Runs the crawler in the background while registering it for graceful stop control."""
    try:
        logging.info(f"Starting background crawl for session: {session_id} (lang={lang})")
        orchestrator = CrawlerOrchestrator(session_id, cfg, lang=lang)
        with crawler_lock:
            active_crawlers[session_id] = orchestrator

        orchestrator.run()
        logging.info(f"Background crawl finished for session: {session_id}")
    except Exception as e:
        logging.error(f"Error in background crawl for session {session_id}: {e}")
    finally:
        with crawler_lock:
            orch = active_crawlers.pop(session_id, None)
            if orch:
                completed_crawlers[session_id] = {
                    "status": "paused" if orch.is_stopped else "complete",
                    "stop_reason": orch.stop_reason or ("Stopped manually" if orch.is_stopped else "Crawl complete"),
                    "logs": list(orch.live_logs),
                    "current_url": orch.current_url,
                    "current_title": orch.current_title,
                    "current_domain": orch.current_domain,
                    "current_summary": orch.current_summary,
                    "current_score": orch.current_score,
                }


@app.get("/")
def read_root():
    return {"status": "ok", "message": "KnowledgeSpider API is running!", "version": "1.0.0"}


@app.post("/api/crawl")
def start_crawl(req: CrawlRequest, background_tasks: BackgroundTasks):
    """Starts a new crawl session with an isolated configuration copy for rocket speed."""
    # Use isolated session config so per-request parameters do NOT mutate the global singleton
    cfg = get_session_config({
        "crawler": {
            "max_depth": req.max_depth,
            "max_sources": req.max_sources,
            "crawl_delay_seconds": 0.0,
            "max_urls_per_query": 8,
        },
        "nlp": {
            "min_content_words": 60,
        }
    })

    # Create the session in the DB
    session = create_session(req.topic, cfg)

    # Start the crawl process in the background
    background_tasks.add_task(background_crawl_task, session.id, cfg, req.lang or "en")

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
    """Returns the stats (sources, topics, terms) for a session along with live telemetry if active."""
    stats = get_session_stats(session_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Session not found or no stats available yet.")
    
    with crawler_lock:
        orch = active_crawlers.get(session_id)
        if orch:
            telemetry = orch.get_live_state()
            status_val = "complete" if telemetry.get("is_finished") else "running"
            stats.update({
                "status": status_val,
                "stop_reason": telemetry.get("stop_reason", ""),
                "current_url": telemetry.get("current_url", ""),
                "current_title": telemetry.get("current_title", ""),
                "current_domain": telemetry.get("current_domain", ""),
                "current_summary": telemetry.get("current_summary", ""),
                "current_score": telemetry.get("current_score", 0.0),
                "live_logs": telemetry.get("logs", []),
            })
        elif session_id in completed_crawlers:
            hist = completed_crawlers[session_id]
            stats.update({
                "status": hist["status"],
                "stop_reason": hist["stop_reason"],
                "current_url": hist.get("current_url", ""),
                "current_title": hist.get("current_title", ""),
                "current_domain": hist.get("current_domain", ""),
                "current_summary": hist.get("current_summary", ""),
                "current_score": hist.get("current_score", 0.0),
                "live_logs": hist.get("logs", []),
            })
        else:
            db_status = stats.get("status", "complete")
            if db_status == "running":
                db_status = "complete" if stats.get("sources_total", 0) > 0 else "paused"
                update_session_status(session_id, db_status)
                stats["status"] = db_status

            default_reason = "اكتملت الجلسة وتمت أرشفة البيانات بنجاح" if db_status == "complete" else "تم إيقاف الجلسة"
            if stats.get("latest_sources"):
                top_s = stats["latest_sources"][0]
                stats.update({
                    "status": db_status,
                    "stop_reason": default_reason,
                    "current_url": top_s["url"],
                    "current_title": top_s["title"],
                    "current_domain": top_s["domain"],
                    "current_summary": top_s["summary"],
                    "current_score": top_s["quality_score"],
                    "live_logs": [],
                })
            else:
                stats.update({
                    "status": db_status,
                    "stop_reason": default_reason,
                    "current_url": "",
                    "current_title": "",
                    "current_domain": "",
                    "current_summary": "",
                    "current_score": 0.0,
                    "live_logs": [],
                })
    return stats


@app.get("/api/session/{session_id}/sources")
def get_session_sources_endpoint(session_id: str):
    """Returns all crawled sources for a specific session with details."""
    sources = get_sources_by_session(session_id)
    return [
        {
            "id": s.id,
            "url": s.url,
            "domain": s.domain,
            "title": s.title or s.url,
            "summary": s.summary or "",
            "quality_score": s.quality_score,
            "depth_level": s.depth_level,
            "word_count": s.word_count,
            "crawled_at": s.crawled_at.isoformat() if s.crawled_at else None,
        }
        for s in sources
    ]


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
def get_graph(session_id: str, lang: Optional[str] = "en"):
    """Returns the knowledge graph summary (nodes, edges, top concepts)."""
    try:
        manager = KnowledgeGraphManager(session_id, lang=lang or "en")
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
