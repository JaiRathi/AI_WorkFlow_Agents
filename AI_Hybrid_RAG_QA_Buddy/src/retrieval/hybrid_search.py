from typing import Optional

from src.ingestion.embedder import Embedder
from config.settings import config


class CitationBuilder:
    @staticmethod
    def build_citation(payload: dict) -> str:
        source_type = payload.get("source_type", "unknown")
        source_file = payload.get("source_file", "unknown")
        line_range = payload.get("line_range", "")
        symbol = payload.get("symbol", "")
        page = payload.get("page")

        if source_type == "jira":
            jira_key = payload.get("metadata", {}).get("jira_key", source_file.replace("jira://", ""))
            return f"[{jira_key}]"

        fname = source_file.rsplit("/", 1)[-1] if "/" in source_file else source_file

        parts = [fname]
        if symbol:
            parts.append(f"::{symbol}")
        if line_range:
            parts.append(f"({line_range})")
        elif page:
            parts.append(f"(p.{page})")

        return f"[{' '.join(parts)}]"

    @staticmethod
    def build_context(chunks: list[dict]) -> str:
        lines = []
        for i, chunk in enumerate(chunks):
            payload = chunk.get("payload", chunk)
            citation = CitationBuilder.build_citation(payload)
            text = payload.get("text", "")
            lines.append(f"--- Source {citation} ---\n{text}")
        return "\n\n".join(lines)

    @staticmethod
    def build_cited_answer(answer: str, chunks: list[dict]) -> dict:
        used_sources = []
        for chunk in chunks:
            payload = chunk.get("payload", chunk)
            citation = CitationBuilder.build_citation(payload)
            source_info = {
                "citation": citation,
                "source_type": payload.get("source_type", ""),
                "source_file": payload.get("source_file", ""),
                "line_range": payload.get("line_range", ""),
                "text_snippet": (payload.get("text", "") or "")[:200],
            }
            used_sources.append(source_info)

        return {
            "answer": answer,
            "sources": used_sources,
            "source_count": len(used_sources),
        }


class HybridRetriever:
    def __init__(self):
        self._embedder = None
        self._citation = None

    @property
    def embedder(self) -> Embedder:
        if self._embedder is None:
            self._embedder = Embedder()
        return self._embedder

    @property
    def citation(self) -> CitationBuilder:
        if self._citation is None:
            self._citation = CitationBuilder()
        return self._citation

    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        source_filter: Optional[list[str]] = None,
    ) -> list[dict]:
        from src.retrieval.qdrant_client import qdrant_manager
        qdrant_manager.ensure_collections()
        k = top_k or config.retrieval.top_k
        query_vector = self.embedder.embed_single(query).tolist()

        filter_condition = None
        if source_filter:
            filter_condition = {
                "must": [
                    {"key": "source_type", "match": {"any": source_filter}}
                ]
            }

        all_results = []
        collections = config.collections

        for source_key, collection_name in collections.items():
            if source_filter and source_key not in source_filter:
                continue

            try:
                count = qdrant_manager.count_points(collection_name)
                if count == 0:
                    continue
            except Exception:
                continue

            results = qdrant_manager.hybrid_search(
                collection_name=collection_name,
                query_text=query,
                query_vector=query_vector,
                top_k=k,
                dense_weight=config.retrieval.dense_weight,
                sparse_weight=config.retrieval.sparse_weight,
                filter_condition=filter_condition,
            )
            all_results.extend(results)

        all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        top_results = all_results[:k]

        if config.retrieval.enable_rerank and len(top_results) > 3:
            top_results = self._rerank(query, top_results)

        return top_results

    def _rerank(self, query: str, results: list[dict]) -> list[dict]:
        try:
            from sentence_transformers import CrossEncoder
            model = CrossEncoder(config.retrieval.rerank_model)
            pairs = [(query, r.get("payload", {}).get("text", "")) for r in results]
            scores = model.predict(pairs)
            for i, r in enumerate(results):
                r["rerank_score"] = float(scores[i])
            results.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)
            return results[:config.retrieval.rerank_top_n]
        except Exception as e:
            print(f"[Reranker] Failed, using original results: {e}")
            return results[:config.retrieval.rerank_top_n]

    def ask(
        self,
        query: str,
        top_k: Optional[int] = None,
        source_filter: Optional[list[str]] = None,
        llm_provider: Optional[str] = None,
        llm_model: Optional[str] = None,
        llm_api_key: Optional[str] = None,
    ) -> dict:
        chunks = self.search(query, top_k, source_filter)
        context = self.citation.build_context(chunks)

        answer = self._generate(query, context, chunks, llm_provider, llm_model, llm_api_key)
        return self.citation.build_cited_answer(answer, chunks)

    def get_context(self, query: str, top_k: Optional[int] = None, source_filter: Optional[list[str]] = None) -> tuple[str, list[dict]]:
        chunks = self.search(query, top_k, source_filter)
        context = self.citation.build_context(chunks)
        return context, chunks

    def _generate(
        self,
        query: str,
        context: str,
        chunks: list[dict],
        llm_provider: Optional[str] = None,
        llm_model: Optional[str] = None,
        llm_api_key: Optional[str] = None,
    ) -> str:
        provider = llm_provider or config.llm.provider
        model = llm_model or config.llm.model
        api_key = llm_api_key or config.llm.api_key

        system_prompt = (
            "You are QABuddy.ai, an expert QA engineering assistant. "
            "Answer using ONLY the provided context below. "
            "If the context does not contain the answer, say 'I could not find relevant information in the knowledge base.' "
            "Always cite sources inline using the [source] markers provided in the context. "
            "Be concise and accurate. Do not make up information."
        )

        user_prompt = (
            f"Context:\n{context}\n\n"
            f"Question: {query}\n\n"
            f"Answer (cite sources as shown in context):"
        )

        if provider == "openai":
            return self._generate_openai(system_prompt, user_prompt, model, api_key)
        elif provider == "anthropic":
            return self._generate_anthropic(system_prompt, user_prompt, model, api_key)
        elif provider == "groq":
            return self._generate_openai_compatible(system_prompt, user_prompt, model, api_key, "https://api.groq.com/openai/v1")
        elif provider == "grok":
            return self._generate_openai_compatible(system_prompt, user_prompt, model, api_key, "https://api.x.ai/v1")
        elif provider == "mistral":
            return self._generate_openai_compatible(system_prompt, user_prompt, model, api_key, "https://api.mistral.ai/v1")
        elif provider == "ollama":
            return self._generate_ollama(system_prompt, user_prompt, model, api_key)
        else:
            return self._generate_fallback(context, chunks)

    def _generate_openai(self, system_prompt: str, user_prompt: str, model: str, api_key: str) -> str:
        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=api_key,
                base_url=config.llm.api_base or None,
            )
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=config.llm.max_tokens,
                temperature=config.llm.temperature,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"[LLM Error: {e}]"

    def _generate_anthropic(self, system_prompt: str, user_prompt: str, model: str, api_key: str) -> str:
        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=api_key)
            response = client.messages.create(
                model=model,
                max_tokens=config.llm.max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            return response.content[0].text
        except Exception as e:
            return f"[LLM Error: {e}]"

    def _generate_ollama(self, system_prompt: str, user_prompt: str, model: str, api_key: str) -> str:
        try:
            from openai import OpenAI
            base_url = api_key if api_key and not api_key.startswith("sk-") else (config.llm.api_base or "http://localhost:11434/v1")
            client = OpenAI(base_url=base_url, api_key="ollama")
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=config.llm.max_tokens,
                temperature=config.llm.temperature,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"[LLM Error: {e}]"

    def _generate_openai_compatible(self, system_prompt: str, user_prompt: str, model: str, api_key: str, base_url: str) -> str:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url=base_url)
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=config.llm.max_tokens,
                temperature=config.llm.temperature,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"[LLM Error: {e}]"

    def _generate_fallback(self, context: str, chunks: list[dict]) -> str:
        if not context.strip():
            return "I could not find any relevant information in the knowledge base."

        chunks_list = []
        for c in chunks:
            payload = c.get("payload", c)
            citation = CitationBuilder.build_citation(payload)
            chunks_list.append(citation)

        sources = ", ".join(chunks_list) if chunks_list else "none"

        if not config.llm.api_key:
            parts = ["## Retrieved Context (No LLM API key configured)\n"]
            parts.append(f"Set an LLM provider and API key in the sidebar or `config/.env`.\n")
            parts.append(f"**{len(chunks_list)} sources matched:** {sources}\n")
            for i, c in enumerate(chunks):
                payload = c.get("payload", c)
                citation = CitationBuilder.build_citation(payload)
                text = (payload.get("text", "") or "")[:500]
                parts.append(f"\n--- Source {citation} ---\n```\n{text}\n```")
            return "\n".join(parts)

        return (
            f"Retrieved context from {len(chunks_list)} sources but generation failed. "
            f"Sources: {sources}"
        )


hybrid_retriever = HybridRetriever()
