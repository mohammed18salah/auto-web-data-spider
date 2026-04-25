# KnowledgeSpider 🕷️

**Autonomous Web Crawling & Knowledge Graph Engine**

KnowledgeSpider is a production-ready, modular Python engine that autonomously crawls the web around a seed topic, extracts NLP-driven knowledge, and builds a queryable graph of interconnected concepts — all persisted to a local SQLite database.

---

## Features

- **Autonomous Crawling** — DuckDuckGo-powered query generation + robots.txt-compliant httpx fetching
- **NLP Pipeline** — spaCy Named Entity & Noun Chunk extraction + sumy TextRank summarisation
- **Quality Scoring** — Configurable composite scoring (length, term density, depth, domain authority)
- **Deduplication** — Thread-safe in-memory + SQLite-backed URL and content-hash deduplication
- **Knowledge Graph** — NetworkX PageRank analysis to surface the most central discovered concepts
- **Session Lifecycle** — Full pause/resume support across process restarts via SQLite
- **Rich CLI** — Typer + Rich command-line interface with an interactive graph REPL
- **Export Engine** — JSON and CSV export for downstream RAG, analysis, or visualization

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 2. Configure

Edit `config.toml` to set crawl depth, source limits, trusted domains, and scoring weights.

### 3. Run a crawl

```bash
# Start a new crawl session
python -m knowledge_spider start "Domain Name System"

# With CLI overrides
python -m knowledge_spider start "Machine Learning" --max-depth 2 --max-sources 50
```

### 4. List sessions

```bash
python -m knowledge_spider sessions
```

### 5. Resume a paused session

```bash
python -m knowledge_spider resume <session-id>
```

### 6. Explore the knowledge graph (interactive REPL)

```bash
python -m knowledge_spider shell <session-id>
```

Inside the shell:
```
spider[abc12345]> summary
spider[abc12345]> explore "DNS"
spider[abc12345]> sources "Domain Name System"
spider[abc12345]> exit
```

### 7. Export results

```bash
# Export to JSON (full graph + sources + terms)
python -m knowledge_spider export <session-id> --format json

# Export to CSV (flat sources table)
python -m knowledge_spider export <session-id> --format csv
```

---

## Architecture

```
knowledge_spider/
├── core/           config.py, session.py
├── query/          query_engine.py       (DuckDuckGo search)
├── crawler/        robots.py, fetcher.py, parser.py,
│                   deduplicator.py, orchestrator.py
├── nlp/            extractor.py (spaCy), summariser.py (sumy)
├── scoring/        scorer.py             (composite quality formula)
├── storage/        models.py, database.py (SQLModel + SQLite)
├── knowledge/      graph.py              (NetworkX + PageRank)
├── export/         exporter.py           (JSON + CSV)
├── cli/            main.py (Typer), shell.py (REPL)
└── utils/          logger.py, hasher.py
```

---

## Configuration (`config.toml`)

| Key | Default | Description |
|---|---|---|
| `crawler.max_depth` | `3` | Max hops from seed topic |
| `crawler.max_sources` | `200` | Stop after N pages collected |
| `crawler.crawl_delay_seconds` | `2.0` | Polite delay between fetches |
| `crawler.respect_robots` | `true` | Honour robots.txt |
| `nlp.min_content_words` | `150` | Skip pages shorter than N words |
| `nlp.summary_sentence_count` | `5` | Sentences in extractive summary |
| `scoring.domain_weight` | `0.35` | Domain authority contribution |
| `scoring.relevance_weight` | `0.35` | Depth decay contribution |

---

## CLI Reference

| Command | Description |
|---|---|
| `spider start <topic>` | Start a new crawl session |
| `spider resume <id>` | Resume a paused session |
| `spider sessions` | List all sessions |
| `spider graph <id>` | Show PageRank graph summary |
| `spider shell <id>` | Launch interactive graph REPL |
| `spider export <id>` | Export session to JSON/CSV |

---

## License

MIT
