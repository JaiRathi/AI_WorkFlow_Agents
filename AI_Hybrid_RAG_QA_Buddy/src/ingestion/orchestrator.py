import uuid
from pathlib import Path
from typing import Optional, Callable

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from config.settings import config, DATA_ROOT
from src.ingestion.parsers.code_parser import CodeParser
from src.ingestion.parsers.spreadsheet_parser import SpreadsheetParser
from src.ingestion.parsers.pdf_parser import PdfParser
from src.ingestion.parsers.transcript_parser import TranscriptParser
from src.ingestion.parsers.log_parser import LogParser
from src.ingestion.chunkers.chunker import Chunker
from src.ingestion.cleaners import Cleaner
from src.ingestion.embedder import Embedder
from src.retrieval.qdrant_client import qdrant_manager

console = Console()


SOURCE_REGISTRY: dict[str, dict] = {
    "selenium": {"dir": DATA_ROOT / "01_selenium_framework", "parser": "code", "source_type": "selenium"},
    "playwright": {"dir": DATA_ROOT / "02_playwright_framework", "parser": "code", "source_type": "playwright"},
    "test_cases": {"dir": DATA_ROOT / "03_test_cases", "parser": "spreadsheet", "source_type": "test_cases"},
    "jira": {"dir": DATA_ROOT / "04_jira_tickets", "parser": "jira_files", "source_type": "jira"},
    "company_docs": {"dir": DATA_ROOT / "05_company_docs", "parser": "pdf", "source_type": "company_docs"},
    "figma": {"dir": DATA_ROOT / "06_figma_exports", "parser": "pdf", "source_type": "figma"},
    "transcripts": {"dir": DATA_ROOT / "07_meeting_transcripts", "parser": "transcript", "source_type": "transcripts"},
    "lucid": {"dir": DATA_ROOT / "08_lucid_charts", "parser": "transcript", "source_type": "lucid"},
    "prd": {"dir": DATA_ROOT / "09_prd_srs_brd_frd", "parser": "pdf", "source_type": "prd"},
    "jenkins": {"dir": DATA_ROOT / "10_jenkins_logs", "parser": "log", "source_type": "jenkins"},
}


class Orchestrator:
    def __init__(self, progress_callback: Optional[Callable[[str, int, int], None]] = None):
        self.cleaner = Cleaner()
        self.chunker = Chunker()
        self.embedder: Optional[Embedder] = None
        self.progress_callback = progress_callback

    def _ensure_embedder(self) -> Embedder:
        if self.embedder is None:
            self.embedder = Embedder()
        return self.embedder

    def ingest_source(self, source_key: str, data_dir: Optional[Path] = None) -> dict:
        entry = SOURCE_REGISTRY.get(source_key)
        if not entry:
            return {"status": "error", "message": f"Unknown source: {source_key}"}

        source_dir = data_dir or entry["dir"]
        if not source_dir.exists():
            return {"status": "error", "message": f"Directory not found: {source_dir}"}

        qdrant_manager.ensure_collections()
        collection_name = config.collections[source_key]
        console.print(f"\n[bold cyan]Ingesting: {source_key}[/bold cyan] → {collection_name}")

        parser = self._get_parser(entry["parser"], source_dir)
        if not parser:
            return {"status": "error", "message": f"No parser for {entry['parser']}"}

        raw_docs = parser.parse()
        console.print(f"  Parsed {len(raw_docs)} documents")

        cleaned = self.cleaner.clean_batch(raw_docs)
        console.print(f"  Cleaned → {len(cleaned)} documents")

        chunks = self.chunker.chunk(cleaned, source_key)
        console.print(f"  Chunked → {len(chunks)} chunks")

        embedder = self._ensure_embedder()
        texts = [c["text"] for c in chunks]
        vectors = embedder.embed(texts)
        console.print(f"  Embedded → {len(vectors)} vectors")

        points = []
        for i, chunk in enumerate(chunks):
            points.append({
                "id": chunk["chunk_id"],
                "vector": vectors[i].tolist(),
                "payload": self.cleaner.build_payload(chunk, source_key),
            })

        batch_size = 100
        for batch_start in range(0, len(points), batch_size):
            batch = points[batch_start:batch_start + batch_size]
            qdrant_manager.upsert_points(collection_name, batch)
            if self.progress_callback:
                self.progress_callback(source_key, batch_start + len(batch), len(points))

        count = qdrant_manager.count_points(collection_name)
        console.print(f"  [green]✓ Indexed {count} points into {collection_name}[/green]")
        return {"status": "ok", "source": source_key, "documents": len(raw_docs), "chunks": len(chunks), "indexed": count}

    def ingest_all(self, sources: Optional[list[str]] = None) -> dict:
        sources = sources or list(SOURCE_REGISTRY.keys())
        results = {}
        for src in sources:
            results[src] = self.ingest_source(src)
        return results

    def ingest_jira_live(self, tickets: list[dict]) -> dict:
        source_key = "jira"
        collection_name = config.collections[source_key]
        console.print(f"\n[bold cyan]Ingesting JIRA (live):[/bold cyan] {len(tickets)} tickets")

        cleaned = self.cleaner.clean_batch(tickets)
        chunks = self.chunker.chunk(cleaned, source_key)

        embedder = self._ensure_embedder()
        texts = [c["text"] for c in chunks]
        vectors = embedder.embed(texts)

        points = []
        for i, chunk in enumerate(chunks):
            points.append({
                "id": chunk["chunk_id"],
                "vector": vectors[i].tolist(),
                "payload": self.cleaner.build_payload(chunk, source_key),
            })

        batch_size = 50
        for batch_start in range(0, len(points), batch_size):
            batch = points[batch_start:batch_start + batch_size]
            qdrant_manager.upsert_points(collection_name, batch)

        count = qdrant_manager.count_points(collection_name)
        console.print(f"  [green]✓ Indexed {count} points into {collection_name}[/green]")
        return {"status": "ok", "source": "jira_live", "tickets": len(tickets), "chunks": len(chunks), "indexed": count}

    def _get_parser(self, parser_type: str, source_dir: Path):
        parsers = {
            "code": CodeParser,
            "spreadsheet": SpreadsheetParser,
            "pdf": PdfParser,
            "transcript": TranscriptParser,
            "log": LogParser,
            "jira_files": TranscriptParser,
        }
        cls = parsers.get(parser_type)
        return cls(source_dir) if cls else None

    def get_index_stats(self) -> dict:
        stats = {}
        for key, collection_name in config.collections.items():
            try:
                count = qdrant_manager.count_points(collection_name)
                stats[key] = count
            except Exception:
                stats[key] = 0
        return stats
