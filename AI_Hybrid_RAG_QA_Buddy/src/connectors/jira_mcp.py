import json
import uuid
from pathlib import Path
from typing import Optional

from config.settings import config, DATA_ROOT


class JiraConnector:
    def __init__(self):
        self.cfg = config.jira
        self._jira_client = None

    @property
    def jira(self):
        if self._jira_client is None:
            try:
                from atlassian import Jira
                self._jira_client = Jira(
                    url=self.cfg.url,
                    username=self.cfg.username,
                    password=self.cfg.api_token,
                    cloud=True,
                )
            except ImportError:
                raise ImportError("atlassian-python-api not installed. Run: pip install atlassian-python-api")
        return self._jira_client

    def fetch_tickets(self, jql: Optional[str] = None, max_results: Optional[int] = None) -> list[dict]:
        query = jql or self.cfg.jql
        limit = max_results or self.cfg.max_results

        all_issues = []
        start_at = 0
        page_size = min(100, limit)

        while start_at < limit:
            issues = self.jira.jql(query, start=start_at, limit=page_size)
            if not issues or not issues.get("issues"):
                break
            all_issues.extend(issues["issues"])
            start_at += len(issues["issues"])
            if len(issues["issues"]) < page_size:
                break

        return all_issues

    def fetch_and_format_tickets(self, jql: Optional[str] = None, max_results: Optional[int] = None) -> list[dict]:
        raw = self.fetch_tickets(jql, max_results)
        documents = []

        for issue in raw:
            fields = issue.get("fields", {})
            key = issue.get("key", "")

            description = ""
            if fields.get("description"):
                description = self._strip_markup(fields["description"])

            comments_text = self._fetch_comments(key) if key else ""

            text_parts = [
                f"JIRA Key: {key}",
                f"Summary: {fields.get('summary', '')}",
                f"Status: {fields.get('status', {}).get('name', '')}",
                f"Type: {fields.get('issuetype', {}).get('name', '')}",
                f"Priority: {fields.get('priority', {}).get('name', '' or 'Unknown') if fields.get('priority') else 'Unknown'}",
                f"Assignee: {fields.get('assignee', {}).get('displayName', 'Unassigned') if fields.get('assignee') else 'Unassigned'}",
                f"Labels: {', '.join(fields.get('labels', []))}",
                f"Description:\n{description}",
            ]
            if comments_text:
                text_parts.append(f"Comments:\n{comments_text}")

            text = "\n".join(text_parts)

            chunk_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"jira:{key}"))
            documents.append({
                "text": text,
                "source_file": f"jira://{key}",
                "chunk_id": chunk_id,
                "type": "jira",
                "metadata": {
                    "jira_key": key,
                    "summary": fields.get("summary", ""),
                    "status": fields.get("status", {}).get("name", ""),
                    "issue_type": fields.get("issuetype", {}).get("name", ""),
                    "priority": fields.get("priority", {}).get("name", "") if fields.get("priority") else "",
                    "labels": fields.get("labels", []),
                    "project": fields.get("project", {}).get("key", ""),
                },
            })

        return documents

    def _fetch_comments(self, issue_key: str) -> str:
        try:
            comments = self.jira.get_issue_comments(issue_key)
            if not comments or not comments.get("comments"):
                return ""
            parts = []
            for comment in comments["comments"]:
                author = comment.get("author", {}).get("displayName", "Unknown")
                body = self._strip_markup(comment.get("body", ""))
                parts.append(f"{author}: {body}")
            return "\n".join(parts)
        except Exception:
            return ""

    @staticmethod
    def _strip_markup(text: str) -> str:
        import re
        if not text:
            return ""
        text = re.sub(r"\{noformat\}.*?\{noformat\}", "", text, flags=re.DOTALL)
        text = re.sub(r"\{code.*?\}.*?\{code\}", "", text, flags=re.DOTALL)
        text = re.sub(r"\{quote\}.*?\{quote\}", "", text, flags=re.DOTALL)
        text = re.sub(r"h\d\.\s", "", text)
        text = re.sub(r"[*_]{1,2}(.*?)[*_]{1,2}", r"\1", text)
        text = re.sub(r"\{\{[^}]*\}\}", "", text)
        text = re.sub(r"\[~[^\]]+\]", "", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def export_tickets_to_file(self, documents: list[dict], output_path: Optional[Path] = None) -> Path:
        output = output_path or DATA_ROOT / "04_jira_tickets" / "jira_export.json"
        serializable = []
        for doc in documents:
            serializable.append({
                "text": doc["text"],
                "metadata": doc.get("metadata", {}),
            })
        output.write_text(json.dumps(serializable, indent=2, ensure_ascii=False))
        print(f"[JIRA] Exported {len(serializable)} tickets to {output}")
        return output


jira_connector = JiraConnector()
