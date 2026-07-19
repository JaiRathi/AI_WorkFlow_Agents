.PHONY: help install run ingest dev clean docker-up docker-down

help:
	@echo "QABuddy.ai — Commands"
	@echo ""
	@echo "  make install      Install Python dependencies"
	@echo "  make run          Start FastAPI server on :8000"
	@echo "  make dev          Start FastAPI + Streamlit concurrently"
	@echo "  make ingest       Run ingestion on all 10 sources"
	@echo "  make ingest-src   Ingest specific source (SRC=selenium)"
	@echo "  make ingest-jira  Fetch live JIRA tickets and index"
	@echo "  make stats        Show Qdrant index stats"
	@echo "  make docker-up    Start all services via Docker Compose"
	@echo "  make docker-down  Stop all Docker services"
	@echo "  make clean        Remove Qdrant storage"

install:
	pip install -r requirements.txt

run:
	PYTHONPATH=. uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

dev:
	@echo "Starting Qdrant..." && \
	( docker ps -a --filter name=qabuddy-qdrant | grep -q qabuddy-qdrant && \
	  docker start qabuddy-qdrant || \
	  docker run -d --name qabuddy-qdrant -p 6333:6333 -p 6334:6334 \
	    -v $(PWD)/qdrant_storage:/qdrant/storage \
	    qdrant/qdrant:latest ) && \
	sleep 2 && \
	echo "Starting FastAPI..." && \
	PYTHONPATH=. uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload & \
	sleep 2 && \
	echo "Starting Streamlit..." && \
	PYTHONPATH=. streamlit run src/frontend/app.py --server.port 8501 & \
	wait

ingest:
	PYTHONPATH=. python -c "\
from src.ingestion.orchestrator import Orchestrator;\
o = Orchestrator();\
print(o.ingest_all())"

ingest-src:
	PYTHONPATH=. python -c "\
from src.ingestion.orchestrator import Orchestrator;\
o = Orchestrator();\
print(o.ingest_all(['$(SRC)']))"

ingest-jira:
	PYTHONPATH=. python -c "\
from src.connectors.jira_mcp import jira_connector;\
from src.ingestion.orchestrator import Orchestrator;\
tickets = jira_connector.fetch_and_format_tickets();\
o = Orchestrator();\
print(o.ingest_jira_live(tickets))"

stats:
	PYTHONPATH=. python -c "\
from src.ingestion.orchestrator import Orchestrator;\
o = Orchestrator();\
import json;\
print(json.dumps(o.get_index_stats(), indent=2))"

docker-up:
	cd docker && docker compose up -d

docker-down:
	cd docker && docker compose down

clean:
	rm -rf qdrant_storage/*
	@echo "Cleaned Qdrant storage"
