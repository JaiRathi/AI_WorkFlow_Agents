from pathlib import Path
from typing import Iterator

from PyPDF2 import PdfReader


class PdfParser:
    def __init__(self, source_dir: Path):
        self.source_dir = Path(source_dir)

    def _iter_files(self) -> Iterator[Path]:
        for ext in ("*.pdf", "*.docx"):
            yield from self.source_dir.rglob(ext)

    def _parse_pdf(self, filepath: Path) -> list[dict]:
        chunks = []
        try:
            reader = PdfReader(str(filepath))
            full_text = []
            for page_idx, page in enumerate(reader.pages):
                text = page.extract_text()
                if text and text.strip():
                    full_text.append({
                        "text": text.strip(),
                        "source_file": str(filepath),
                        "page": page_idx + 1,
                        "type": "document",
                        "format": "pdf",
                    })
            chunks.extend(full_text)
        except Exception as e:
            print(f"[PdfParser] Error reading {filepath}: {e}")
        return chunks

    def _parse_docx(self, filepath: Path) -> list[dict]:
        chunks = []
        try:
            from docx import Document
            doc = Document(str(filepath))
            full_text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
            if full_text.strip():
                chunks.append({
                    "text": full_text,
                    "source_file": str(filepath),
                    "type": "document",
                    "format": "docx",
                })
        except Exception as e:
            print(f"[PdfParser] Error reading {filepath}: {e}")
        return chunks

    def parse(self) -> list[dict]:
        results = []
        for filepath in self._iter_files():
            suffix = filepath.suffix.lower()
            if suffix == ".pdf":
                results.extend(self._parse_pdf(filepath))
            elif suffix == ".docx":
                results.extend(self._parse_docx(filepath))
        return results
