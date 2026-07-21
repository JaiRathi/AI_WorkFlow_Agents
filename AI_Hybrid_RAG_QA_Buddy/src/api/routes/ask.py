from fastapi import APIRouter, HTTPException

from src.api.schemas import AskRequest, AskResponse
from src.retrieval.hybrid_search import hybrid_retriever

router = APIRouter(prefix="/api", tags=["ask"])


@router.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    result = hybrid_retriever.ask(
        query=request.query,
        top_k=request.top_k,
        source_filter=request.source_filter,
        llm_provider=request.llm_provider,
        llm_model=request.llm_model,
        llm_api_key=request.llm_api_key,
    )
    return AskResponse(**result)
