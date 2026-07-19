from pathlib import Path
from typing import Iterator


class TranscriptParser:
    SUPPORTED_EXTS = {".txt", ".vtt", ".srt", ".md", ".markdown"}

    def __init__(self, source_dir: Path):
        self.source_dir = Path(source_dir)

    def _iter_files(self) -> Iterator[Path]:
        for ext in self.SUPPORTED_EXTS:
            yield from self.source_dir.rglob(f"*{ext}")

    def _parse_vtt_srt(self, filepath: Path) -> list[dict]:
        chunks = []
        try:
            text = filepath.read_text(encoding="utf-8", errors="replace")
            lines = text.split("\n")
            dialogue_lines = []
            in_header = True
            for line in lines:
                stripped = line.strip()
                if not stripped or stripped.isdigit() or "-->" in stripped or stripped.startswith("WEBVTT"):
                    if not in_header and dialogue_lines:
                        chunk_text = " ".join(dialogue_lines)
                        if chunk_text.strip():
                            chunks.append({
                                "text": chunk_text,
                                "source_file": str(filepath),
                                "type": "transcript",
                                "format": filepath.suffix.lstrip("."),
                            })
                        dialogue_lines = []
                    in_header = False if stripped and not stripped.startswith("WEBVTT") else in_header
                    continue
                in_header = False
                dialogue_lines.append(stripped)
            if dialogue_lines:
                chunk_text = " ".join(dialogue_lines)
                if chunk_text.strip():
                    chunks.append({
                        "text": chunk_text,
                        "source_file": str(filepath),
                        "type": "transcript",
                        "format": filepath.suffix.lstrip("."),
                    })
        except Exception as e:
            print(f"[TranscriptParser] Error reading {filepath}: {e}")
        return chunks

    def _parse_text(self, filepath: Path) -> list[dict]:
        try:
            content = filepath.read_text(encoding="utf-8", errors="replace")
            if content.strip():
                return [{
                    "text": content.strip(),
                    "source_file": str(filepath),
                    "type": "transcript",
                    "format": filepath.suffix.lstrip("."),
                }]
        except Exception as e:
            print(f"[TranscriptParser] Error reading {filepath}: {e}")
        return []

    def parse(self) -> list[dict]:
        results = []
        for filepath in self._iter_files():
            suffix = filepath.suffix.lower()
            if suffix in (".vtt", ".srt"):
                results.extend(self._parse_vtt_srt(filepath))
            else:
                results.extend(self._parse_text(filepath))
        return results
