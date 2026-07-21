import os
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = PROJECT_ROOT / "data"


@dataclass
class EmbeddingConfig:
    model_name: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-base-en-v1.5")
    device: str = os.getenv("EMBEDDING_DEVICE", "cpu")
    batch_size: int = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))
    dimension: int = 768


@dataclass
class QdrantConfig:
    url: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    api_key: str = os.getenv("QDRANT_API_KEY", "")
    prefer_grpc: bool = False
    distance_metric: str = "Cosine"


@dataclass
class ChunkingConfig:
    code: dict = field(default_factory=lambda: {"chunk_size": 600, "chunk_overlap": 100})
    test_case: dict = field(default_factory=lambda: {"chunk_size": 300, "chunk_overlap": 0})
    pdf: dict = field(default_factory=lambda: {"chunk_size": 500, "chunk_overlap": 50})
    transcript: dict = field(default_factory=lambda: {"chunk_size": 800, "chunk_overlap": 100})
    jira: dict = field(default_factory=lambda: {"chunk_size": 500, "chunk_overlap": 50})
    markdown: dict = field(default_factory=lambda: {"chunk_size": 500, "chunk_overlap": 50})
    log: dict = field(default_factory=lambda: {"chunk_size": 300, "chunk_overlap": 0})
    lucid: dict = field(default_factory=lambda: {"chunk_size": 300, "chunk_overlap": 0})
    default: dict = field(default_factory=lambda: {"chunk_size": 500, "chunk_overlap": 50})


@dataclass
class RetrievalConfig:
    top_k: int = int(os.getenv("RETRIEVAL_TOP_K", "5"))
    dense_weight: float = float(os.getenv("DENSE_WEIGHT", "0.6"))
    sparse_weight: float = float(os.getenv("SPARSE_WEIGHT", "0.4"))
    enable_rerank: bool = os.getenv("ENABLE_RERANK", "false").lower() == "true"
    rerank_model: str = os.getenv("RERANK_MODEL", "BAAI/bge-reranker-base")
    rerank_top_n: int = int(os.getenv("RERANK_TOP_N", "3"))


@dataclass
class LLMConfig:
    provider: str = os.getenv("LLM_PROVIDER", "openai")
    model: str = os.getenv("LLM_MODEL", "gpt-4o")
    api_key: str = os.getenv("OPENAI_API_KEY", os.getenv("ANTHROPIC_API_KEY", ""))
    api_base: str = os.getenv("LLM_API_BASE", "")
    max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "1024"))
    temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.1"))


@dataclass
class JiraConfig:
    url: str = os.getenv("JIRA_URL", "")
    username: str = os.getenv("JIRA_USERNAME", "")
    api_token: str = os.getenv("JIRA_API_TOKEN", "")
    jql: str = os.getenv("JIRA_JQL", "project = YOUR_PROJECT ORDER BY created DESC")
    max_results: int = int(os.getenv("JIRA_MAX_RESULTS", "1000"))


@dataclass
class Config:
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    qdrant: QdrantConfig = field(default_factory=QdrantConfig)
    chunking: ChunkingConfig = field(default_factory=ChunkingConfig)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    jira: JiraConfig = field(default_factory=JiraConfig)

    collection_prefix: str = os.getenv("COLLECTION_PREFIX", "qabuddy")

    @property
    def collections(self) -> dict[str, str]:
        prefix = self.collection_prefix
        return {
            "selenium": f"{prefix}_selenium",
            "playwright": f"{prefix}_playwright",
            "test_cases": f"{prefix}_test_cases",
            "jira": f"{prefix}_jira",
            "company_docs": f"{prefix}_company_docs",
            "figma": f"{prefix}_figma",
            "transcripts": f"{prefix}_transcripts",
            "lucid": f"{prefix}_lucid",
            "prd": f"{prefix}_prd",
            "jenkins": f"{prefix}_jenkins",
        }


config = Config()
