# QABuddy.ai — Hybrid RAG for QA Engineers

Self-hosted, multi-source RAG system that answers QA questions with **citations** grounded in your frameworks, test cases, JIRA tickets, PRDs, and operational logs.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start Qdrant (Docker)
docker run -d --name qabuddy-qdrant -p 6333:6333 -p 6334:6334 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  qdrant/qdrant:latest

# 3. Configure your environment
cp config/.env.example config/.env
# Edit config/.env with your API keys and JIRA credentials

# 4. Place your data in the data/ folders, then ingest
make ingest

# 5. Start the server
make run

# 6. Open the chat UI
# Streamlit: http://localhost:8501
# API docs: http://localhost:8000/docs
```

## Architecture

See **[architecture.html](architecture.html)** for the full visual architecture, technology decisions, chunking strategies, and API reference.

```
User → Streamlit Chat UI → FastAPI /api/ask
                                ↓
                          HybridRetriever
                         ┌──────┼──────┐
                    Dense       ↓     Sparse
                  (BGE 768d)  RRF   (BM25)
                         └──────┼──────┘
                                ↓
                            Qdrant DB
                                ↓
                          LLM Generation
                         (OpenAI / Claude / Ollama)
                                ↓
                         Cited Answer + Sources
```

## Data Sources (10)

| # | Source | Folder |
|---|--------|--------|
| 1 | Selenium Framework | `data/01_selenium_framework/` |
| 2 | Playwright Framework | `data/02_playwright_framework/` |
| 3 | Test Cases (CSV/XLSX) | `data/03_test_cases/` |
| 4 | JIRA Tickets | `data/04_jira_tickets/` or live via API |
| 5 | Company Docs (PDF/MD) | `data/05_company_docs/` |
| 6 | Figma Exports | `data/06_figma_exports/` (Phase 2) |
| 7 | Meeting Transcripts | `data/07_meeting_transcripts/` |
| 8 | Lucid Charts | `data/08_lucid_charts/` |
| 9 | PRD/SRS/BRD/FRD | `data/09_prd_srs_brd_frd/` |
| 10 | Jenkins Logs | `data/10_jenkins_logs/` |

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/health` | Health check + index stats |
| `POST` | `/api/ask` | Ask a QA question → cited answer |
| `POST` | `/api/ingest` | Trigger ingestion for all/specific sources |
| `POST` | `/api/ingest/jira` | Fetch live JIRA tickets + index |
| `GET` | `/api/stats` | Per-collection document counts |

## Makefile Commands

```bash
make help          # Show all commands
make dev           # Start FastAPI + Streamlit + Qdrant concurrently
make ingest        # Ingest all 10 data sources
make ingest-src SRC=selenium   # Ingest a specific source
make ingest-jira   # Fetch live JIRA tickets
make stats         # Show index statistics
make docker-up     # Docker Compose all services
make clean         # Clear Qdrant storage
```

## Deployment

```bash
# On your DigitalOcean droplet:
git clone <this-repo>
cp config/.env.example config/.env
# Edit .env with your keys
make docker-up
```

Access at:
- **Chat UI:** `http://<droplet-ip>:8501`
- **API Docs:** `http://<droplet-ip>:8000/docs`

## Phase 2 (Planned)

- Hourly auto-ingestion (detect new files, commits, JIRA tickets)
- Figma design ingestion (ER diagrams, wireframes, user guides)
