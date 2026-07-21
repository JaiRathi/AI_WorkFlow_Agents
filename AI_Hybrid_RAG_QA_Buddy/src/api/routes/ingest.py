from fastapi import APIRouter, HTTPException

from src.api.schemas import IngestRequest, IngestResponse, JiraIngestRequest, StatsResponse
from src.ingestion.orchestrator import Orchestrator, SOURCE_REGISTRY
from src.connectors.jira_mcp import jira_connector

router = APIRouter(prefix="/api", tags=["ingest"])


@router.post("/ingest", response_model=IngestResponse)
async def ingest(request: IngestRequest):
    orchestrator = Orchestrator()
    if request.sources:
        invalid = [s for s in request.sources if s not in SOURCE_REGISTRY]
        if invalid:
            raise HTTPException(status_code=400, detail=f"Unknown sources: {invalid}")
    results = orchestrator.ingest_all(request.sources)
    return IngestResponse(status="ok", results=results)


@router.post("/ingest/jira", response_model=IngestResponse)
async def ingest_jira(request: JiraIngestRequest):
    try:
        tickets = jira_connector.fetch_and_format_tickets(
            jql=request.jql or None,
            max_results=request.max_results or None,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"JIRA fetch failed: {str(e)}")

    if not tickets:
        return IngestResponse(status="ok", results={"jira": {"tickets": 0, "message": "No tickets returned"}})

    orchestrator = Orchestrator()
    result = orchestrator.ingest_jira_live(tickets)
    return IngestResponse(status="ok", results={"jira": result})


@router.get("/stats", response_model=StatsResponse)
async def stats():
    orchestrator = Orchestrator()
    collections = orchestrator.get_index_stats()
    return StatsResponse(collections=collections)
