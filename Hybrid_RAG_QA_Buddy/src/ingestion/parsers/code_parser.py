import ast
import re
from pathlib import Path
from typing import Iterator


class CodeParser:
    SUFFIX_MAP = {
        ".py": "python", ".js": "javascript", ".ts": "typescript",
        ".java": "java", ".go": "go", ".rs": "rust", ".rb": "ruby",
        ".php": "php", ".c": "c", ".cpp": "cpp", ".h": "c",
        ".cs": "csharp", ".swift": "swift", ".kt": "kotlin",
        ".scala": "scala", ".sh": "bash", ".yaml": "yaml",
        ".yml": "yaml", ".json": "json", ".xml": "xml",
        ".sql": "sql", ".tf": "hcl", ".dockerfile": "dockerfile",
    }

    def __init__(self, source_dir: Path):
        self.source_dir = Path(source_dir)

    def _iter_files(self) -> Iterator[Path]:
        exclude_patterns = {".git", "__pycache__", "node_modules", ".venv",
                           "venv", ".idea", ".vscode", "dist", "build",
                           ".tox", ".eggs", "*.egg-info"}
        for fp in self.source_dir.rglob("*"):
            if fp.is_file() and not any(p in fp.parts for p in exclude_patterns):
                yield fp

    def _get_language(self, filepath: Path) -> str:
        suffix = filepath.suffix.lower()
        if suffix:
            return self.SUFFIX_MAP.get(suffix, "text")
        name_lower = filepath.name.lower()
        for keyword, lang in self.SUFFIX_MAP.items():
            if keyword.startswith(".") and name_lower.endswith(keyword):
                return lang
        return "text"

    def _parse_python(self, content: str, filepath: Path) -> list[dict]:
        chunks = []
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return [self._raw_chunk(content, filepath)]

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                start_line = node.lineno
                end_line = node.end_lineno or start_line
                lines = content.split("\n")[start_line - 1:end_line]
                chunk_text = "\n".join(lines)
                chunks.append({
                    "text": chunk_text,
                    "source_file": str(filepath),
                    "line_range": f"L{start_line}-L{end_line}",
                    "symbol": node.name,
                    "type": "function",
                    "language": "python",
                })
            elif isinstance(node, ast.ClassDef):
                start_line = node.lineno
                end_line = node.end_lineno or start_line
                lines = content.split("\n")[start_line - 1:end_line]
                chunk_text = "\n".join(lines)
                chunks.append({
                    "text": chunk_text,
                    "source_file": str(filepath),
                    "line_range": f"L{start_line}-L{end_line}",
                    "symbol": node.name,
                    "type": "class",
                    "language": "python",
                })

        if not chunks:
            return [self._raw_chunk(content, filepath)]
        return chunks

    def _parse_generic(self, content: str, filepath: Path) -> list[dict]:
        lang = self._get_language(filepath)
        pattern = re.compile(
            r"^\s*(?:def |function |func |async function |class |"
            r"public class |public static |private static |protected )",
            re.MULTILINE,
        )
        lines = content.split("\n")
        chunks = []
        current_start = 0
        for i, line in enumerate(lines):
            if pattern.match(line) and i > current_start:
                chunk_text = "\n".join(lines[current_start:i])
                if chunk_text.strip():
                    chunks.append({
                        "text": chunk_text,
                        "source_file": str(filepath),
                        "line_range": f"L{current_start + 1}-L{i}",
                        "type": "code_block",
                        "language": lang,
                    })
                current_start = i
        remainder = "\n".join(lines[current_start:])
        if remainder.strip():
            chunks.append({
                "text": remainder,
                "source_file": str(filepath),
                "line_range": f"L{current_start + 1}-L{len(lines)}",
                "type": "code_block",
                "language": lang,
            })

        if not chunks:
            return [self._raw_chunk(content, filepath)]
        return chunks

    def _raw_chunk(self, content: str, filepath: Path) -> dict:
        return {
            "text": content,
            "source_file": str(filepath),
            "line_range": "L1-L" + str(len(content.split("\n"))),
            "type": "file",
            "language": self._get_language(filepath),
        }

    def parse(self) -> list[dict]:
        results = []
        for filepath in self._iter_files():
            try:
                content = filepath.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue

            if not content.strip():
                continue

            if filepath.suffix == ".py":
                chunks = self._parse_python(content, filepath)
            else:
                chunks = self._parse_generic(content, filepath)

            results.extend(chunks)
        return results
