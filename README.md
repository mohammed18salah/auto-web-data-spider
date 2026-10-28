<div align="center">

# 🕷️ KnowledgeSpider

### Autonomous Web Crawling, NLP Entity Extraction & Knowledge Graph Discovery Engine

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/Python-3.11%20|%203.12%20|%203.13-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19.0-61DAFB.svg?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6.svg?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Electron](https://img.shields.io/badge/Electron-Desktop-47848F.svg?style=for-the-badge&logo=electron&logoColor=white)](https://www.electronjs.org/)
[![NetworkX](https://img.shields.io/badge/NetworkX-Knowledge%20Graph-FF6F00.svg?style=for-the-badge)](https://networkx.org/)
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-brightgreen.svg?style=for-the-badge)](https://github.com/mohammed18salah/data-spider/pulls)

<p align="center">
  <b>Transform any seed topic into an interconnected, queryable knowledge graph — 100% local, autonomous, and free of proprietary API tokens.</b>
</p>

[Key Features](#-key-features) •
[Why KnowledgeSpider? (Comparison)](#-why-knowledgespider-competitive-comparison) •
[Architecture](#-system-architecture) •
[Quick Start](#-quick-start) •
[Desktop App](#-desktop-app--ui) •
[CLI & Interactive Shell](#-cli--interactive-shell) •
[API Reference](#-rest-api-reference) •
[Roadmap](#-open-source-roadmap)

---

</div>

## 📖 Overview

**KnowledgeSpider** is an open-source autonomous web discovery and knowledge-synthesis system. Given any single keyword or seed topic (e.g. *"Quantum Computing"*, *"Cybersecurity Frameworks"*, or *"Domain Name System"*), KnowledgeSpider autonomously:

1. **Searches & Explores**: Queries privacy-focused search engines (DuckDuckGo) and discovers authoritative web sources.
2. **Fetches & Sanitizes**: Parses HTML content, adheres strictly to `robots.txt`, rotates user agents, and filters out boilerplate/low-value markup.
3. **NLP Knowledge Pipeline**: Leverages **spaCy** for Named Entity Recognition (NER) and noun chunking, coupled with **sumy TextRank** for extractive multi-sentence summaries.
4. **Calculates Multi-Dimensional Quality Scores**: Rates each source from `0.0` to `1.0` using domain authority, text density, relevance decay, and content length.
5. **Synthesizes Directed Knowledge Graphs**: Constructs high-dimensional topic relationship graphs using **NetworkX**, computing **PageRank** and centrality to reveal foundational domain concepts.
6. **Local-First Persistence**: Stores complete crawl history, nodes, edges, terms, and session snapshots into a lightweight, local **SQLite** database via **SQLModel**.
7. **Dual-Interface Access**: Operate via a cross-platform **Electron + React 19** desktop GUI (featuring dark mode and Arabic/English localization) or through an interactive **CLI REPL Shell**.

---

## ⚡ Why KnowledgeSpider? Competitive Comparison

Most existing web scrapers either require manual rule-writing, dump unstructured plain text, or rely on expensive, non-deterministic cloud LLMs. Here is how KnowledgeSpider compares against standard scrapers and modern AI crawling platforms:

| Feature / Dimension | 🕷️ **KnowledgeSpider** | 🕷️ **Scrapy** | 🤖 **AutoGPT / Agent Scrapers** | 🔥 **Crawl4AI / Firecrawl** | 🌐 **Neo4j / Memgraph Stacks** |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Autonomous Topic Discovery** | ✅ **Built-in** (automatic search & branch) | ❌ Manual spiders & link extractors | ⚠️ Yes, but prone to drifting | ❌ URL-based scraping only | ❌ Graph only, no crawler |
| **NLP Entity & Noun Extraction** | ✅ **Built-in (spaCy local)** | ❌ Requires custom pipelines | ⚠️ Cloud LLM tokens | ⚠️ Markdown / LLM extraction | ❌ Manual ingestion |
| **Extractive Summarization** | ✅ **Built-in (TextRank)** | ❌ None | ⚠️ Expensive LLM tokens | ⚠️ Markdown summary | ❌ None |
| **Integrated Knowledge Graph** | ✅ **Built-in (NetworkX + PageRank)** | ❌ None | ❌ None (raw text output) | ❌ None | ✅ Yes (requires DB server) |
| **Cost per 1,000 Pages** | 🟢 **$0.00 (100% Free & Local)** | 🟢 $0.00 | 🔴 $5.00 – $30.00 (OpenAI/Anthropic) | 🟠 Token/Subscription cost | 🟠 Server infrastructure cost |
| **Desktop GUI Included** | ✅ **Yes (Electron + React 19)** | ❌ Terminal only / Scrapyd | ❌ Web dashboard or terminal | ⚠️ Web dashboard | ⚠️ Web browser tool |
| **Multilingual UI (AR / EN)** | ✅ **Yes (RTL + LTR Native)** | ❌ None | ❌ English-first | ❌ English-first | ❌ English-first |
| **Local-First & Zero Telemetry** | ✅ **SQLite (Single-file DB)** | ✅ Files / SQLite | ❌ Cloud telemetry / Third-party APIs | ⚠️ Hosted or local Docker | ❌ Heavy Docker instances |
| **Deterministic Quality Scoring** | ✅ **Configurable Formula** | ❌ Manual coding | ❌ Hallucinatory / Non-deterministic | ❌ Basic heuristics | ❌ None |
| **Interactive Terminal Shell** | ✅ **Rich REPL Shell** | ⚠️ Scrapy Shell (page only) | ❌ Chat loop | ❌ None | ⚠️ Cypher shell |

---

## 🌟 What Makes KnowledgeSpider a Standout Open-Source Project?

- **Zero Cloud Lock-in & Privacy First**: No OpenAI/Anthropic API keys required. Everything runs locally on your machine using spaCy, NLTK, and sumy.
- **RAG-Ready Structured Outputs**: Directly feeds modern Vector Databases and RAG pipelines (LangChain, LlamaIndex, Ollama, ChromaDB) with pre-extracted entities and PageRank-weighted summaries.
- **Hardened Security Architecture**:
  - Electron uses `contextIsolation: true`, `nodeIntegration: false`, and `sandbox: true`.
  - FastAPI backend enforces strict origin whitelisting (No wildcard `*` CORS exploits).
  - SQLModel prepared statements prevent SQL injection.
- **Resilient Process Architecture**:
  - Background crawler task with **Graceful Stop** (`/api/crawl/stop`) so crawls can be paused and resumed without data loss.
  - Isolated session configurations (`get_session_config`) that prevent global singleton pollution.
- **Accessible to Both Developers and Researchers**:
  - Developers can integrate via Python SDK, REST API, or CLI.
  - Researchers and non-programmers can launch the one-click desktop app with visual progress and live charts.

---

## 🏗️ System Architecture

The following diagram illustrates the complete end-to-end data processing lifecycle inside KnowledgeSpider:

```mermaid
flowchart TD
    subgraph UI ["Desktop & Client Layer"]
        GUI["Electron + React 19 UI<br/>(Glassmorphic, RTL/LTR)"]
        CLI["Typer CLI &<br/>KnowledgeShell REPL"]
    end

    subgraph API ["FastAPI Backend (Localhost:8000)"]
        Router["REST Router & CORS Guard"]
        Reg["Active Crawlers Registry<br/>(Graceful Stop / Pause)"]
        CfgMgr["Config Manager & Isolation"]
    end

    subgraph Engine ["KnowledgeSpider Core Engine"]
        Orch["Crawler Orchestrator"]
        Q["Priority Topic Queue<br/>(depth ASC, relevance DESC)"]
        SE["DuckDuckGo Query Engine"]
        Fetch["HTTP Fetcher & Robots Guard<br/>(httpx + User-Agent Pool)"]
        Dedup["Deduplicator (Content SHA-256 + URL)"]
        NLP["NLP Pipeline<br/>(spaCy NER + TextRank Summarizer)"]
        Score["Quality Scorer (0.0 - 1.0)"]
    end

    subgraph Storage ["Persistent Storage & Graph Layer"]
        DB[("SQLite Database<br/>(knowledge_spider.db)")]
        KG["NetworkX DiGraph<br/>(PageRank & Centrality Analysis)"]
        Exp["Exporter Engine<br/>(JSON, CSV, GEXF)"]
    end

    GUI <-->|REST API + Preload IPC| Router
    CLI <-->|Direct Python Import| Orch
    Router --> Reg
    Router --> Orch
    CfgMgr -.-> Orch

    Orch --> Q
    Q --> SE
    SE --> Fetch
    Fetch --> Dedup
    Dedup --> NLP
    NLP --> Score
    Score --> DB
    DB <--> KG
    KG --> Exp
    Exp --> GUI
```

---

## 📂 Repository Layout

```text
data-spider/
├── backend/
│   ├── knowledge_spider/       # Core Python Engine
│   │   ├── cli/                # Typer CLI and Interactive Shell (REPL)
│   │   ├── core/               # Configuration, Session Lifecycle, Queue Manager, Orchestrator
│   │   ├── crawler/            # Fetcher (httpx), Parser (BS4), Robots parser, Deduplicator
│   │   ├── expansion/          # Autonomous Query & Topic expansion
│   │   ├── export/             # JSON & CSV Exporter modules
│   │   ├── knowledge/          # NetworkX Graph Manager, PageRank, Centrality
│   │   ├── nlp/                # spaCy Named Entity Extraction & sumy TextRank Summarizer
│   │   ├── query/              # DuckDuckGo search integration
│   │   ├── scoring/            # Composite multi-factor source quality scoring
│   │   ├── storage/            # SQLModel database models, SQLite engine & CRUD
│   │   └── utils/              # Thread-safe logging, SHA-256 hashing, language detection
│   ├── tests/                  # Comprehensive test suite (Unit & Integration)
│   ├── config.toml             # Central runtime configuration
│   ├── main.py                 # FastAPI server with CORS & Graceful Stop
│   ├── pyproject.toml          # Standard Python packaging configuration
│   └── requirements.txt        # Backend dependencies
│
├── frontend/
│   ├── electron/               # Electron Main process & secure Preload bridge
│   │   ├── main.js             # Electron main process (spawns Python backend)
│   │   └── preload.cjs         # ContextBridge security isolation script
│   ├── src/                    # React 19 Frontend
│   │   ├── App.tsx             # Main Application dashboard & History viewer
│   │   ├── index.css           # Glassmorphic UI Design System (RTL/LTR, Dark/Light)
│   │   └── main.tsx            # React application entry point
│   ├── package.json            # Frontend & Electron scripts and dependencies
│   └── vite.config.ts          # Vite build and development configuration
│
└── README.md                   # Project documentation
```

---

## 🚀 Quick Start

### Prerequisites

- **Python**: `3.11` or higher
- **Node.js**: `18.0.0` or higher
- **npm** or **pnpm** / **yarn**

---

### Step 1: Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate a Python virtual environment:
   ```bash
   # Windows (PowerShell)
   python -m venv .venv
   .venv\Scripts\Activate.ps1

   # Linux / macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install backend dependencies and the spaCy language model:
   ```bash
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

4. *(Optional)* Install in editable mode:
   ```bash
   pip install -e .
   ```

5. Run the FastAPI development server:
   ```bash
   python main.py
   # Or using uvicorn:
   uvicorn main:app --host 127.0.0.1 --port 8000 --reload
   ```
   > The API will be accessible at: `http://127.0.0.1:8000` (Interactive docs at `/docs`).

---

### Step 2: Frontend & Desktop App Setup

1. In a separate terminal, navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. **Run in Web Browser mode**:
   ```bash
   npm run dev
   ```
   > Access the web dashboard at `http://localhost:5173`.

4. **Run as Desktop App (Electron)**:
   ```bash
   npm run electron:dev
   ```
   > Automatically boots both the Vite dev server and the Electron desktop application.

---

## 🖥️ Desktop App & UI

The KnowledgeSpider desktop GUI is engineered for high productivity and intuitive visual monitoring:

- **Bilingual Interface**: Seamlessly switch between **العربية (RTL)** and **English (LTR)** with a single click.
- **Glassmorphic Dark & Light Modes**: Tailored color palettes with ambient mesh gradients and smooth transitions.
- **Live Crawl Monitoring**: Real-time timer, analyzed sources counter, active search queries, and expandable logs.
- **Depth & Source Limit Controls**: Adjust parameters on the fly via smooth slider inputs.
- **One-Click Data Export**: Instant download of structured JSON exports.
- **History Management**: Review previous crawl runs, examine status badges, and safely delete obsolete sessions.

---

## 💻 CLI & Interactive Shell

KnowledgeSpider includes a full-featured Command Line Interface built with **Typer** and **Rich**.

### Start a Crawl from Terminal

```bash
# Basic crawl
python -m knowledge_spider start "Artificial Intelligence"

# Custom depth and source limits
python -m knowledge_spider start "Distributed Systems" --max-depth 2 --max-sources 25
```

### Inspect Stored Sessions

```bash
python -m knowledge_spider sessions
```

### Resume a Paused Crawl

```bash
python -m knowledge_spider resume <session-id>
```

### Interactive Knowledge Graph REPL

Explore nodes, relationships, and source summaries directly in your terminal:

```bash
python -m knowledge_spider shell <session-id>
```

Inside the interactive shell:
```text
spider[c4a189f2]> summary
   Total Nodes: 14
   Total Edges: 22
   Top Concepts (PageRank):
     1. Domain Name System (Score: 0.284)
     2. Authoritative Name Server (Score: 0.198)
     3. DNSSEC (Score: 0.142)

spider[c4a189f2]> explore "DNSSEC"
   Discovered connections from 'DNSSEC':
     → Public Key Cryptography (weight: 0.92)
     → Root Zone (weight: 0.85)

spider[c4a189f2]> sources "DNSSEC"
   [1] RFC 4033 - DNS Security Introduction (Score: 0.94)
       Summary: An introduction to the DNS Security Extensions...

spider[c4a189f2]> exit
```

---

## ⚙️ Configuration (`config.toml`)

All runtime behavior is controlled centrally via `backend/config.toml`:

```toml
[crawler]
max_depth            = 3        # Maximum recursion depth from seed topic
max_sources          = 200      # Stop after harvesting N high-quality pages
time_limit_minutes   = 60       # Global timeout safeguard
crawl_delay_seconds  = 2.0      # Respectful rate-limiting delay between requests
max_urls_per_query   = 5        # URLs grabbed per search query
respect_robots       = true     # Respect robots.txt directives
trusted_only         = false    # If true, restrict to trusted_domains

[nlp]
min_content_words      = 150    # Skip thin/junk content
relevance_threshold    = 0.45   # Minimum keyword match to retain topic
max_topics_per_page    = 8      # Maximum child subtopics to branch per page
summary_sentence_count = 5      # Sentences in TextRank extractive summary

[scoring]
domain_weight    = 0.35         # Weight of domain authority score
content_weight   = 0.15         # Weight of word count & term richness
relevance_weight = 0.35         # Weight of semantic relevance to seed
freshness_weight = 0.15         # Weight of recent discovery / timestamp
# Note: Scoring weights must sum to exactly 1.0

[trusted_domains]
domains = [
  "wikipedia.org",
  "developer.mozilla.org",
  "arxiv.org",
  "rfc-editor.org",
  "docs.python.org",
  "github.com",
]
```

---

## 🔌 REST API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | System health and API version |
| `POST` | `/api/crawl` | Start a new background crawl session with parameters |
| `POST` | `/api/crawl/stop` | Gracefully stop all active crawler instances |
| `POST` | `/api/crawl/{session_id}/stop` | Gracefully stop a specific session |
| `GET` | `/api/session/{session_id}` | Fetch real-time metrics (sources, topics, edges, quality) |
| `DELETE`| `/api/session/{session_id}` | Cascade delete session and all associated graph data |
| `GET` | `/api/graph/{session_id}` | Retrieve graph topology, nodes, edges, and PageRank summary |
| `GET` | `/api/export/{session_id}` | Retrieve full structured JSON export payload |
| `GET` | `/api/sessions` | List all previous crawl sessions |
| `GET` | `/api/config` | Retrieve current runtime system configuration |
| `POST` | `/api/config` | Dynamically update runtime system settings |

---

## 🧪 Testing & Validation

KnowledgeSpider includes a 22-step automated verification suite covering database models, NLP summarizers, deduplication, robots parsing, and graph algorithms:

```bash
cd backend

# Run the test suite
python tests/test_new_fixes.py
python tests/test_step0.py
python tests/test_step1.py
python tests/test_step2.py
python tests/test_step3.py
```

To validate the frontend build:
```bash
cd frontend
npm run build
```

---

## 🗺️ Open-Source Roadmap

- [x] **v1.0 (Current)**:
  - Autonomous search-driven crawling loop
  - spaCy NER and TextRank summarization
  - NetworkX knowledge graph synthesis and PageRank scoring
  - Local SQLite persistence with pause/resume support
  - Electron + React 19 desktop GUI with Dark/Light and Arabic/English modes
  - Hardened Electron IPC & strict FastAPI CORS
- [ ] **v1.1 (Upcoming)**:
  - 3D interactive knowledge graph visualizer (Three.js / React Force Graph) inside the desktop app.
  - Export to GEXF / GraphML directly from the UI.
  - Native PDF document crawling and text extraction.
- [ ] **v1.2**:
  - Optional local LLM integration via **Ollama** for question-answering over discovered knowledge graphs.
  - One-click export to Vector Databases (Chroma, Qdrant, LanceDB).

---

## 🤝 Contributing

Contributions are warmly welcomed! KnowledgeSpider thrives on community ideas, bug reports, and pull requests.

1. **Fork** the repository.
2. **Create** a feature branch: `git checkout -b feat/amazing-feature`.
3. **Commit** your changes: `git commit -m 'feat: add amazing feature'`.
4. **Push** to your branch: `git push origin feat/amazing-feature`.
5. **Open** a Pull Request.

Please make sure to run tests and follow clean code conventions before opening PRs.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details. Free for commercial and personal use.

---

<div align="center">
  <sub>Built with ❤️ by the KnowledgeSpider Team. If you find this project useful, please consider giving it a ⭐ on GitHub!</sub>
</div>
