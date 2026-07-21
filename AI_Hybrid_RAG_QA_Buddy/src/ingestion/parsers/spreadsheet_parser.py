import csv
from pathlib import Path
from typing import Iterator

import pandas as pd


class SpreadsheetParser:
    def __init__(self, source_dir: Path):
        self.source_dir = Path(source_dir)

    def _iter_files(self) -> Iterator[Path]:
        for ext in ("*.csv", "*.xlsx", "*.xls"):
            yield from self.source_dir.rglob(ext)

    def _parse_csv(self, filepath: Path) -> list[dict]:
        chunks = []
        try:
            with open(filepath, encoding="utf-8-sig", errors="replace") as f:
                reader = csv.DictReader(f)
                if not reader.fieldnames:
                    return chunks
                for row_idx, row in enumerate(reader):
                    text_parts = []
                    for key, value in row.items():
                        if value and str(value).strip():
                            text_parts.append(f"{key}: {value}")
                    text = "\n".join(text_parts)
                    if text.strip():
                        chunks.append({
                            "text": text,
                            "source_file": str(filepath),
                            "row_index": row_idx,
                            "type": "test_case",
                            "metadata": {k: str(v) for k, v in row.items() if v},
                        })
        except Exception as e:
            print(f"[SpreadsheetParser] Error reading {filepath}: {e}")
        return chunks

    def _parse_excel(self, filepath: Path) -> list[dict]:
        chunks = []
        try:
            xl = pd.ExcelFile(filepath)
            for sheet_name in xl.sheet_names:
                df = xl.parse(sheet_name)
                df = df.where(pd.notnull(df), None)
                for row_idx, row in df.iterrows():
                    text_parts = []
                    for col, value in row.items():
                        if value is not None and str(value).strip():
                            text_parts.append(f"{col}: {value}")
                    text = "\n".join(text_parts)
                    if text.strip():
                        chunks.append({
                            "text": text,
                            "source_file": str(filepath),
                            "sheet": sheet_name,
                            "row_index": int(row_idx),
                            "type": "test_case",
                            "metadata": {str(k): str(v) for k, v in row.items() if v is not None},
                        })
        except Exception as e:
            print(f"[SpreadsheetParser] Error reading {filepath}: {e}")
        return chunks

    def parse(self) -> list[dict]:
        results = []
        for filepath in self._iter_files():
            suffix = filepath.suffix.lower()
            if suffix == ".csv":
                results.extend(self._parse_csv(filepath))
            elif suffix in (".xlsx", ".xls"):
                results.extend(self._parse_excel(filepath))
        return results
