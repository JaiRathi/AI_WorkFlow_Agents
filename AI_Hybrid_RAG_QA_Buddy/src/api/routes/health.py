from fastapi import APIRouter

from src.api.schemas import HealthResponse
from src.ingestion.orchestrator import Orchestrator
from config.settings import config

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health():
    from src.retrieval.qdrant_client import qdrant_manager
    qdrant_status = "ok"
    try:
        qdrant_manager.ensure_collections()
        qdrant_manager.client.get_collections()
    except Exception:
        qdrant_status = "unreachable"

    orchestrator = Orchestrator()
    collections = orchestrator.get_index_stats()

    return HealthResponse(
        status="healthy" if qdrant_status == "ok" else "degraded",
        qdrant=qdrant_status,
        embedding_model=config.embedding.model_name,
        llm_provider=config.llm.provider,
        collections=collections,
    )
