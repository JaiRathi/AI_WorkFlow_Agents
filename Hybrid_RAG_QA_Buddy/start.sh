#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${CYAN}[QABuddy]${NC} $1"; }
ok()   { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err()  { echo -e "${RED}[✗]${NC} $1"; }

cleanup() {
    log "Shutting down services..."
    [ -n "${API_PID:-}" ] && kill "$API_PID" 2>/dev/null && ok "FastAPI stopped"
    [ -n "${STREAMLIT_PID:-}" ] && kill "$STREAMLIT_PID" 2>/dev/null && ok "Streamlit stopped"
    [ -n "${QDRANT_PID:-}" ] && kill "$QDRANT_PID" 2>/dev/null && ok "Qdrant stopped"
    log "Cleanup complete."
}
trap cleanup EXIT INT TERM

# ---- Parse args ----
INGEST=false
NO_QDRANT=false
PORT_API=8000
PORT_UI=8501
PORT_QDRANT_HTTP=6333
PORT_QDRANT_GRPC=6334

usage() {
    cat <<EOF
Usage: ./start.sh [OPTIONS]

Options:
  --ingest          Run full ingestion after startup
  --no-qdrant       Skip starting Qdrant (assume already running)
  --api-port PORT   FastAPI port (default: 8000)
  --ui-port PORT    Streamlit port (default: 8501)
  -h, --help        Show this help

Examples:
  ./start.sh                        # Start all services
  ./start.sh --ingest               # Start + ingest all sources
  ./start.sh --no-qdrant            # Start API + UI only (Qdrant already on :6333)
EOF
    exit 0
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --ingest)    INGEST=true; shift ;;
        --no-qdrant) NO_QDRANT=true; shift ;;
        --api-port)  PORT_API="$2"; shift 2 ;;
        --ui-port)   PORT_UI="$2"; shift 2 ;;
        -h|--help)   usage ;;
        *)           err "Unknown option: $1"; usage ;;
    esac
done

# ---- Prerequisites ----
if ! command -v python3 &>/dev/null; then
    err "python3 not found. Install Python 3.11+ first."
    exit 1
fi

if [ ! -f "config/.env" ]; then
    warn "config/.env not found. Copying from .env.example..."
    cp config/.env.example config/.env
    warn "Edit config/.env with your API keys before using /ask."
fi

export $(grep -v '^#' config/.env | xargs) 2>/dev/null || true
export PYTHONPATH="$PROJECT_ROOT"

# ---- Qdrant ----
if [ "$NO_QDRANT" = false ]; then
    if command -v docker &>/dev/null; then
        if docker ps --filter "name=qabuddy-qdrant" --format '{{.Names}}' | grep -q qabuddy-qdrant; then
            ok "Qdrant container already running"
        elif docker ps -a --filter "name=qabuddy-qdrant" --format '{{.Names}}' | grep -q qabuddy-qdrant; then
            log "Starting existing Qdrant container..."
            docker start qabuddy-qdrant
        else
            log "Creating Qdrant container (ports ${PORT_QDRANT_HTTP}:6333, ${PORT_QDRANT_GRPC}:6334)..."
            docker run -d --name qabuddy-qdrant \
                -p "${PORT_QDRANT_HTTP}:6333" \
                -p "${PORT_QDRANT_GRPC}:6334" \
                -v "$PROJECT_ROOT/qdrant_storage:/qdrant/storage" \
                qdrant/qdrant:latest
        fi
    else
        err "Docker not found. Install Docker to run Qdrant, or start Qdrant manually and use --no-qdrant."
        exit 1
    fi

    log "Waiting for Qdrant health check..."
    for i in $(seq 1 20); do
        if curl -sf "http://localhost:${PORT_QDRANT_HTTP}/healthz" >/dev/null 2>&1; then
            ok "Qdrant is ready"
            break
        fi
        if [ "$i" -eq 20 ]; then
            err "Qdrant failed to start. Check: docker logs qabuddy-qdrant"
            exit 1
        fi
        sleep 1
    done
fi

# ---- Install Python deps if needed ----
if ! python3 -c "import fastapi" 2>/dev/null; then
    log "Installing Python dependencies..."
    python3 -m pip install -r requirements.txt --quiet
    ok "Dependencies installed"
fi

# ---- Ingest ----
if [ "$INGEST" = true ]; then
    log "Running ingestion on all sources..."
    python3 -c "
from src.ingestion.orchestrator import Orchestrator
o = Orchestrator()
results = o.ingest_all()
for k, v in results.items():
    status = v.get('status', '?')
    chunks = v.get('chunks', 0)
    print(f'  {k}: {status} ({chunks} chunks)')
" || warn "Ingestion completed with some errors — check logs above"
fi

# ---- Start FastAPI ----
log "Starting FastAPI on :${PORT_API}..."
python3 -m uvicorn src.api.main:app \
    --host 0.0.0.0 \
    --port "$PORT_API" \
    --reload \
    --log-level info &
API_PID=$!
sleep 2

if ! kill -0 "$API_PID" 2>/dev/null; then
    err "FastAPI failed to start"
    exit 1
fi
ok "FastAPI running (PID $API_PID) → http://localhost:${PORT_API}"
ok "API docs → http://localhost:${PORT_API}/docs"

# ---- Start Streamlit ----
log "Starting Streamlit on :${PORT_UI}..."
QABUDDY_API_URL="http://localhost:${PORT_API}" \
python3 -m streamlit run src/frontend/app.py \
    --server.port "$PORT_UI" \
    --server.address 0.0.0.0 \
    --server.headless true \
    --browser.gatherUsageStats false &
STREAMLIT_PID=$!
sleep 3

if ! kill -0 "$STREAMLIT_PID" 2>/dev/null; then
    err "Streamlit failed to start"
    exit 1
fi
ok "Streamlit running (PID $STREAMLIT_PID) → http://localhost:${PORT_UI}"

# ---- Ready ----
echo ""
echo -e "${GREEN}══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  QABuddy.ai is running!${NC}"
echo -e "${GREEN}══════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  Chat UI:    ${CYAN}http://localhost:${PORT_UI}${NC}"
echo -e "  API Docs:   ${CYAN}http://localhost:${PORT_API}/docs${NC}"
echo -e "  Health:     ${CYAN}http://localhost:${PORT_API}/health${NC}"
echo ""
echo -e "  Press ${YELLOW}Ctrl+C${NC} to stop all services."
echo ""

wait
