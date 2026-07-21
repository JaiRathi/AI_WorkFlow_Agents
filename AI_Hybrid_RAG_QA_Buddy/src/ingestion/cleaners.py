import re


class Cleaner:
    EXCESS_WHITESPACE = re.compile(r"[ \t]+")
    EXCESS_NEWLINES = re.compile(r"\n{3,}")

    QA_TERMINOLOGY = {
        "smoke": "smoke",
        "regression": "regression",
        "sanity": "sanity",
        "uat": "UAT",
        "e2e": "end-to-end",
        "rca": "root cause analysis",
        "rtm": "requirements traceability matrix",
        "prd": "product requirements document",
        "srs": "software requirements specification",
        "brd": "business requirements document",
        "frd": "functional requirements document",
        "tcid": "test case ID",
        "tc": "test case",
        "def": "defect",
        "p0": "priority 0",
        "p1": "priority 1",
        "p2": "priority 2",
        "flaky": "flaky test",
    }

    def clean(self, text: str, doc_type: str = "document") -> str:
        text = text.strip()
        text = self.EXCESS_WHITESPACE.sub(" ", text)
        text = self.EXCESS_NEWLINES.sub("\n\n", text)

        if doc_type == "log":
            text = re.sub(r"\[0m|\[3[1-7]m|\[9[0-9]m|\[1m|\[0K", "", text)
            text = re.sub(r"\x1b\[\d+(;\d+)*m", "", text)

        if doc_type == "code":
            text = text.rstrip()

        return text

    def clean_batch(self, docs: list[dict]) -> list[dict]:
        cleaned = []
        for doc in docs:
            doc_type = doc.get("type", "document")
            text = self.clean(doc.get("text", ""), doc_type)
            if text.strip():
                doc["text"] = text
                cleaned.append(doc)
        return cleaned

    def build_payload(self, doc: dict, source_type: str) -> dict:
        return {
            "text": doc.get("text", ""),
            "source_type": source_type,
            "source_file": doc.get("source_file", ""),
            "chunk_id": doc.get("chunk_id", ""),
            "chunk_index": doc.get("chunk_index", 0),
            "line_range": doc.get("line_range", ""),
            "symbol": doc.get("symbol", ""),
            "language": doc.get("language", ""),
            "page": doc.get("page", None),
            "metadata": doc.get("metadata", {}),
        }

    def build_payloads(self, docs: list[dict], source_type: str) -> list[dict]:
        return [self.build_payload(d, source_type) for d in docs]
