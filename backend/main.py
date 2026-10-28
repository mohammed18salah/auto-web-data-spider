from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import json
import logging
from pathlib import Path

# Add the root directory to sys.path so we can import knowledge_spider
sys.path.insert(0, str(Path(__file__).resolve().parent / "spider"))

from knowledge_spider.core.config import get_config
from knowledge_spider.core.session import create_session
from knowledge_spider.storage.database import create_db_and_tables, get_session_stats, list_sessions
from knowledge_spider.crawler.orchestrator import CrawlerOrchestrator
from knowledge_spider.knowledge.graph import KnowledgeGraphManager
from knowledge_spider.export.exporter import DataExporter
from knowledge_spider.utils.logger import setup_logger

# Setup Database and Logger on startup
create_db_and_tables()
setup_logger("api_backend")

app = FastAPI(title="KnowledgeSpider API", description="Backend API for Electron App")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "file://",
        "*"
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CrawlRequest(BaseModel):
    topic: str
    max_depth: int = 1
    max_sources: int = 5

def background_crawl_task(session_id: str, cfg):
    """Runs the crawler in the background."""
    try:
        logging.info(f"Starting background crawl for session: {session_id}")
        orchestrator = CrawlerOrchestrator(session_id, cfg)
        orchestrator.run()
        logging.info(f"Background crawl finished for session: {session_id}")
    except Exception as e:
        logging.error(f"Error in background crawl: {e}")

@app.get("/")
def read_root():
    return {"status": "ok", "message": "KnowledgeSpider API is running!"}

@app.post("/api/crawl")
def start_crawl(req: CrawlRequest, background_tasks: BackgroundTasks):
    """Starts a new crawl session for a given topic."""
    cfg = get_config()
    cfg.crawler.max_depth = req.max_depth
    cfg.crawler.max_sources = req.max_sources
    
    # Create the session in the DB
    session = create_session(req.topic, cfg)
    
    # Start the crawl process in the background so the UI doesn't freeze
    background_tasks.add_task(background_crawl_task, session.id, cfg)
    
    return {
        "status": "started",
        "session_id": session.id,
        "topic": req.topic,
        "message": "Crawl started in the background."
    }

@app.get("/api/session/{session_id}")
def get_session_info(session_id: str):
    """Returns the stats (sources, topics, terms) for a session."""
    stats = get_session_stats(session_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Session not found or no stats available yet.")
    return stats

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

if __name__ == "__main__":
    import uvicorn
    # Run the server locally on port 8000
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
