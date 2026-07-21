from pydantic import BaseModel, Field
from typing import Optional


class AskRequest(BaseModel):
    query: str = Field(..., description="The QA question to answer")
    top_k: Optional[int] = Field(default=5, description="Number of chunks to retrieve")
    source_filter: Optional[list[str]] = Field(default=None, description="Filter by source type (selenium, jira, etc)")
    llm_provider: Optional[str] = Field(default=None, description="Override LLM provider: openai, anthropic, ollama")
    llm_model: Optional[str] = Field(default=None, description="Override LLM model name")
    llm_api_key: Optional[str] = Field(default=None, description="Override LLM API key")


class SettingsRequest(BaseModel):
    llm_provider: Optional[str] = Field(default=None, description="openai, anthropic, or ollama")
    llm_model: Optional[str] = Field(default=None)
    llm_api_key: Optional[str] = Field(default=None)
    top_k: Optional[int] = Field(default=None)
    temperature: Optional[float] = Field(default=None)
    max_tokens: Optional[int] = Field(default=None)


class AskResponse(BaseModel):
    answer: str
    sources: list[dict]
    source_count: int


class IngestRequest(BaseModel):
    sources: Optional[list[str]] = Field(default=None, description="List of sources to ingest, or omit for all")


class IngestResponse(BaseModel):
    status: str
    results: dict


class StatsResponse(BaseModel):
    status: str = "ok"
    collections: dict


class JiraIngestRequest(BaseModel):
    jql: Optional[str] = Field(default=None, description="JQL query string")
    max_results: Optional[int] = Field(default=None, description="Max tickets to fetch")


class HealthResponse(BaseModel):
    status: str
    qdrant: str
    embedding_model: str
    llm_provider: str
    collections: dict
