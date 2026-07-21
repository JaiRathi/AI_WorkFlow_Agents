import os
import sys

import streamlit as st
import requests
import pandas as pd

API_BASE = os.getenv("QABUDDY_API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="QABuddy.ai — QA Knowledge Base",
    page_icon="🛡️",
    layout="wide",
)

st.title("🛡️ QABuddy.ai")
st.caption("Hybrid RAG for QA Engineers — ask anything about your frameworks, test cases, JIRA, and docs.")

with st.expander("📐 Architecture & Flow", expanded=False):
    cols = st.columns([2, 1])
    with cols[0]:
        st.markdown("""
```
┌──────────────────────────────────────────────────────────────────┐
│                    QABuddy.ai — Self-Hosted VPS                   │
│                                                                   │
│  QA Engineer ──► Streamlit :8501 ──► FastAPI :8000               │
│                                          │                        │
│                   ┌──────────────────────┼──────────────────┐    │
│                   │     HybridRetriever                       │    │
│                   │  ┌──────────┐  ┌──────────┐  ┌────────┐  │    │
│                   │  │  Dense   │  │  RRF     │  │  LLM   │  │    │
│                   │  │  BGE 768d│──┤  Fusion  │──┤  Gen   │  │    │
│                   │  └──────────┘  └──────────┘  └────────┘  │    │
│                   └──────────────────────┬──────────────────┘    │
│                                          │                        │
│                   ┌──────────────────────┼──────────────────┐    │
│                   │   Qdrant Vector DB   │  :6333            │    │
│                   │   10 Collections     │  Dense + Sparse   │    │
│                   └──────────────────────┼──────────────────┘    │
│                                          │                        │
│  DATA ──► Parse ──► Clean ──► Chunk ──► Embed ──► Index         │
│  10 sources · 5 parsers · per-type chunking · BGE · UUID ids     │
└──────────────────────────────────────────────────────────────────┘
```
""")
    with cols[1]:
        st.markdown("**How it works:**")
        st.markdown("""
1. **Ingest** — Parse files from `data/` folders
2. **Chunk** — Split by source type (code, CSV rows, PDFs, transcripts, logs)
3. **Embed** — BGE-base-en-v1.5 (768-dim)
4. **Index** — Store in Qdrant with metadata
5. **Search** — Dense + Sparse hybrid retrieval
6. **Generate** — LLM answer with inline citations

**6 LLM Providers:** OpenAI · Anthropic · Grok · Groq · Mistral · Ollama
""")
    st.caption("Full diagram → [architecture.html](architecture.html) · PNG → [architecture.png](architecture.png)")

st.divider()

with st.sidebar:
    st.subheader("🤖 LLM Settings")
    llm_provider = st.selectbox(
        "Provider",
        options=["openai", "anthropic", "grok", "groq", "mistral", "ollama"],
        index=0,
    )
    if llm_provider == "openai":
        llm_model = st.text_input("Model", value="gpt-4o", placeholder="gpt-4o / gpt-4o-mini")
        llm_api_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
    elif llm_provider == "anthropic":
        llm_model = st.text_input("Model", value="claude-3-5-sonnet-20241022")
        llm_api_key = st.text_input("Anthropic API Key", type="password", placeholder="sk-ant-...")
    elif llm_provider == "grok":
        llm_model = st.text_input("Model", value="grok-2", placeholder="grok-2 / grok-2-latest")
        llm_api_key = st.text_input("xAI API Key", type="password", placeholder="xai-...")
    elif llm_provider == "groq":
        llm_model = st.text_input("Model", value="llama3-70b-8192", placeholder="llama3-70b / mixtral-8x7b")
        llm_api_key = st.text_input("Groq API Key", type="password", placeholder="gsk_...")
    elif llm_provider == "mistral":
        llm_model = st.text_input("Model", value="mistral-large-latest", placeholder="mistral-large-latest / codestral")
        llm_api_key = st.text_input("Mistral API Key", type="password", placeholder="...")
    else:
        llm_model = st.text_input("Model", value="llama3", placeholder="llama3 / mistral")
        llm_api_key = st.text_input("Ollama Base URL", value="http://localhost:11434/v1")

    st.divider()

    st.subheader("🔍 Search Filters")
    source_filter = st.multiselect(
        "Limit to sources",
        options=[
            "selenium", "playwright", "test_cases", "jira",
            "company_docs", "transcripts", "lucid", "prd", "jenkins",
        ],
        default=None,
        help="Leave empty to search all sources",
    )
    top_k = st.slider("Chunks to retrieve", min_value=1, max_value=20, value=5)

    st.divider()

    st.subheader("📊 Index Stats")
    if st.button("Refresh Stats"):
        try:
            resp = requests.get(f"{API_BASE}/api/stats", timeout=5)
            if resp.ok:
                stats = resp.json().get("collections", {})
                df = pd.DataFrame(
                    [{"Source": k, "Documents": v} for k, v in stats.items()]
                )
                st.dataframe(df, hide_index=True, use_container_width=True)
        except Exception:
            st.warning("Cannot reach API")

    st.divider()
    st.markdown(
        "**QABuddy.ai** v1.0 — Self-hosted on your VPS\n\n"
        "Sources: Selenium, Playwright, Test Cases, JIRA, "
        "Company Docs, Transcripts, Lucid Charts, PRDs, Jenkins Logs"
    )

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "sources" in msg and msg["sources"]:
            with st.expander("📎 Sources"):
                for src in msg["sources"]:
                    st.caption(f"{src['citation']} — {src['source_file']}")

if prompt := st.chat_input("Ask a QA question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Searching knowledge base..."):
            try:
                payload = {"query": prompt, "top_k": top_k}
                if source_filter:
                    payload["source_filter"] = source_filter
                if llm_api_key.strip():
                    payload["llm_provider"] = llm_provider
                    payload["llm_model"] = llm_model
                    payload["llm_api_key"] = llm_api_key

                resp = requests.post(
                    f"{API_BASE}/api/ask",
                    json=payload,
                    timeout=60,
                )

                if resp.ok:
                    data = resp.json()
                    answer = data.get("answer", "No answer returned.")
                    sources = data.get("sources", [])

                    st.markdown(answer)

                    if sources:
                        with st.expander("📎 Sources"):
                            for src in sources:
                                snippet = src.get("text_snippet", "")[:100]
                                st.caption(
                                    f"**{src['citation']}** — {src['source_file']}\n\n"
                                    f"_{snippet}..._"
                                )

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources,
                    })
                else:
                    err_msg = f"⚠️ API error: {resp.status_code} — {resp.text[:200]}"
                    st.error(err_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": err_msg,
                    })

            except requests.exceptions.ConnectionError:
                err_msg = "⚠️ Cannot reach QABuddy API at " + API_BASE
                st.error(err_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": err_msg,
                })
            except Exception as e:
                err_msg = f"⚠️ Error: {str(e)}"
                st.error(err_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": err_msg,
                })
