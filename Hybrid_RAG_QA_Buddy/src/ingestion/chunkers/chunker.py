import re
import uuid
from typing import Optional

from langchain_text_splitters import RecursiveCharacterTextSplitter

from config.settings import config


class Chunker:
    SEPARATORS_MAP = {
        "python": ["\ndef ", "\nclass ", "\n\n", "\n", " ", ""],
        "code": ["\nfunction ", "\nclass ", "\ndef ", "\n\n", "\n", " ", ""],
        "markdown": ["\n## ", "\n### ", "\n#### ", "\n\n", "\n", " ", ""],
        "document": ["\n\n", "\n", ". ", " ", ""],
        "transcript": ["\n\n", "\n", ". ", " ", ""],
    }

    def __init__(self):
        self.cfg = config.chunking

    def _chunk_size_for(self, doc_type: str) -> int:
        return getattr(self.cfg, doc_type, self.cfg.default)["chunk_size"]

    def _overlap_for(self, doc_type: str) -> int:
        return getattr(self.cfg, doc_type, self.cfg.default)["chunk_overlap"]

    NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")

    def _make_id(self, source_file: str, chunk_index: int, text: str) -> str:
        return str(uuid.uuid5(self.NAMESPACE, f"{source_file}:{chunk_index}:{text[:100]}"))

    def _pick_separators(self, language: Optional[str] = None) -> list[str]:
        if language and language in self.SEPARATORS_MAP:
            return self.SEPARATORS_MAP[language]
        return self.SEPARATORS_MAP["document"]

    def chunk_code(self, doc: dict, chunk_index: int) -> list[dict]:
        text = doc["text"]
        chunk_size = self._chunk_size_for("code")
        chunk_overlap = self._overlap_for("code")

        if len(text) <= chunk_size:
            doc["chunk_id"] = self._make_id(doc.get("source_file", ""), chunk_index, text)
            doc["chunk_index"] = chunk_index
            return [doc]

        language = doc.get("language", "code")
        separators = self._pick_separators(language)
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators,
        )
        sub_texts = splitter.split_text(text)
        chunks = []
        for i, sub in enumerate(sub_texts):
            c = {**doc, "text": sub, "chunk_index": chunk_index + i}
            c["chunk_id"] = self._make_id(c.get("source_file", ""), chunk_index + i, sub)
            chunks.append(c)
        return chunks

    def chunk_test_case(self, doc: dict, chunk_index: int) -> list[dict]:
        doc["chunk_id"] = self._make_id(doc.get("source_file", ""), chunk_index, doc["text"])
        doc["chunk_index"] = chunk_index
        return [doc]

    def chunk_document(self, doc: dict, chunk_index: int) -> list[dict]:
        text = doc["text"]
        chunk_size = self._chunk_size_for("pdf")
        chunk_overlap = self._overlap_for("pdf")

        if len(text) <= chunk_size:
            doc["chunk_id"] = self._make_id(doc.get("source_file", ""), chunk_index, text)
            doc["chunk_index"] = chunk_index
            return [doc]

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=self._pick_separators("document"),
        )
        sub_texts = splitter.split_text(text)
        chunks = []
        for i, sub in enumerate(sub_texts):
            c = {**doc, "text": sub, "chunk_index": chunk_index + i}
            c["chunk_id"] = self._make_id(c.get("source_file", ""), chunk_index + i, sub)
            chunks.append(c)
        return chunks

    def chunk_transcript(self, doc: dict, chunk_index: int) -> list[dict]:
        text = doc["text"]
        chunk_size = self._chunk_size_for("transcript")
        chunk_overlap = self._overlap_for("transcript")

        if len(text) <= chunk_size:
            doc["chunk_id"] = self._make_id(doc.get("source_file", ""), chunk_index, text)
            doc["chunk_index"] = chunk_index
            return [doc]

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=self._pick_separators("transcript"),
        )
        sub_texts = splitter.split_text(text)
        chunks = []
        for i, sub in enumerate(sub_texts):
            c = {**doc, "text": sub, "chunk_index": chunk_index + i}
            c["chunk_id"] = self._make_id(c.get("source_file", ""), chunk_index + i, sub)
            chunks.append(c)
        return chunks

    def chunk_log(self, doc: dict, chunk_index: int) -> list[dict]:
        text = doc["text"]
        chunk_size = self._chunk_size_for("log")

        if len(text) <= chunk_size:
            doc["chunk_id"] = self._make_id(doc.get("source_file", ""), chunk_index, text)
            doc["chunk_index"] = chunk_index
            return [doc]
        return [doc]

    def chunk_lucid(self, doc: dict, chunk_index: int) -> list[dict]:
        doc["chunk_id"] = self._make_id(doc.get("source_file", ""), chunk_index, doc["text"])
        doc["chunk_index"] = chunk_index
        return [doc]

    def chunk(self, docs: list[dict], source_type: str) -> list[dict]:
        all_chunks = []
        chunk_index = 0
        for doc in docs:
            t = doc.get("type", source_type)
            if t == "function" or t == "class" or t == "code_block":
                sub = self.chunk_code(doc, chunk_index)
            elif t == "test_case":
                sub = self.chunk_test_case(doc, chunk_index)
            elif t == "transcript":
                sub = self.chunk_transcript(doc, chunk_index)
            elif t == "log":
                sub = self.chunk_log(doc, chunk_index)
            elif source_type in ("lucid",):
                sub = self.chunk_lucid(doc, chunk_index)
            else:
                sub = self.chunk_document(doc, chunk_index)

            all_chunks.extend(sub)
            chunk_index += max(len(sub), 1)
        return all_chunks
