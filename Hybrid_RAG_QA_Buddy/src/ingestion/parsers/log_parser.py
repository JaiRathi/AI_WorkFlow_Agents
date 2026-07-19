import re
from pathlib import Path
from typing import Iterator


class LogParser:
    TIMESTAMP_PATTERN = re.compile(
        r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}"
    )

    def __init__(self, source_dir: Path):
        self.source_dir = Path(source_dir)

    def _iter_files(self) -> Iterator[Path]:
        for ext in ("*.log", "*.txt"):
            yield from self.source_dir.rglob(ext)

    def _split_by_blocks(self, content: str, filepath: Path) -> list[dict]:
        lines = content.split("\n")
        chunks = []
        current_block: list[str] = []
        current_start = 0

        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                if current_block:
                    chunks.append({
                        "text": "\n".join(current_block),
                        "source_file": str(filepath),
                        "line_range": f"L{current_start + 1}-L{i}",
                        "type": "log",
                    })
                    current_block = []
                continue

            is_new_block = (
                self.TIMESTAMP_PATTERN.match(stripped)
                or stripped.startswith("ERROR")
                or stripped.startswith("WARN")
                or stripped.startswith("FAIL")
                or stripped.startswith("BUILD")
                or stripped.startswith("====")
            )

            if is_new_block and current_block:
                chunks.append({
                    "text": "\n".join(current_block),
                    "source_file": str(filepath),
                    "line_range": f"L{current_start + 1}-L{i}",
                    "type": "log",
                })
                current_block = []
                current_start = i

            current_block.append(line)

        if current_block:
            chunks.append({
                "text": "\n".join(current_block),
                "source_file": str(filepath),
                "line_range": f"L{current_start + 1}-L{len(lines)}",
                "type": "log",
            })

        if not chunks:
            return [{
                "text": content,
                "source_file": str(filepath),
                "line_range": f"L1-L{len(lines)}",
                "type": "log",
            }]
        return chunks

    def parse(self) -> list[dict]:
        results = []
        for filepath in self._iter_files():
            try:
                content = filepath.read_text(encoding="utf-8", errors="replace")
                if content.strip():
                    results.extend(self._split_by_blocks(content, filepath))
            except Exception as e:
                print(f"[LogParser] Error reading {filepath}: {e}")
        return results
