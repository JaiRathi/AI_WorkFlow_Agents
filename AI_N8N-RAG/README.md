# ⚡ AI3X Basic RAG (n8n Workflow)

A complete **n8n RAG (Retrieval-Augmented Generation)** workflow featuring dual-phase architecture:
1. **Phase 1 — Ingestion Pipeline:** Web form submission for document uploads (`.pdf`, `.csv`, `.json`, `.docx`, `.txt`, `.html`), text chunking via Recursive Character Text Splitter, OpenAI embeddings (`text-embedding-3-small`), and Pinecone vector store indexing.
2. **Phase 2 — RAG Retrieval & QA Agent:** Conversational chat interface powered by an n8n LangChain agent, OpenAI chat model (`gpt-4o-mini`/`gpt-5-mini`), windowed memory buffer, and Pinecone vector search tool with source file citations.

---

## 📐 Workflow Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ PHASE 1: INGESTION PIPELINE                                                                │
│                                                                                             │
│  ┌───────────────────────┐      ┌─────────────────────────┐      ┌───────────────────────┐  │
│  │   Form Submission     │ ───> │   Default Data Loader   │ ───> │ Store to Pinecone DB  │  │
│  │ (.pdf,.csv,.txt,etc.) │      │ (Extract Meta + Chunks) │      │  (Index: test-1536)   │  │
│  └───────────────────────┘      └────────────┬────────────┘      └───────────▲───────────┘  │
│                                              │                               │              │
│                                              ▼                               │              │
│                                 ┌─────────────────────────┐     ┌────────────┴──────────┐   │
│                                 │ Recursive Text Splitter │     │ OpenAI Embeddings     │   │
│                                 │  (Overlap: 200 chars)   │     │ (text-embedding-small)│   │
│                                 └─────────────────────────┘     └───────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ PHASE 2: RAG FETCHING & CHAT AGENT                                                         │
│                                                                                             │
│  ┌───────────────────────┐               ┌───────────────────────┐                          │
│  │ Chat Message Received │ ────────────> │       RAG Agent       │                          │
│  └───────────────────────┘               │ (Strict Citation Rule)│                          │
│                                          └───────▲───────▲───────┘                          │
│                                                  │       │                                  │
│                   ┌──────────────────────────────┘       └───────────────────────────┐      │
│                   │                                                                  │      │
│     ┌─────────────┴────────────┐     ┌──────────────────────────┐     ┌──────────────┴────┐ │
│     │   Brain (OpenAI LLM)     │     │    Model Chat Memory     │     │ Pinecone Vector   │ │
│     │   (gpt-4o-mini/gpt-5)    │     │  (Window Buffer Memory)  │     │ Search Tool (k=3) │ │
│     └──────────────────────────┘     └──────────────────────────┘     └───────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🧩 Component Breakdown

| Node Name | Node Type | Category | Configuration & Parameters |
| :--- | :--- | :--- | :--- |
| **On form submission** | `n8n-nodes-base.formTrigger` | Trigger | Form Title: "Upload Documents for RAG"<br>Accepted File Types: `.pdf,.csv,.json,.docs,.txt,.html` |
| **Default Data Loader** | `@n8n/n8n-nodes-langchain.documentDefaultDataLoader` | LangChain | Custom metadata extraction: `fileName`, `uploadedAt` timestamp |
| **Recursive Character Text Splitter** | `@n8n/n8n-nodes-langchain.textSplitterRecursiveCharacterTextSplitter` | LangChain | `chunkOverlap`: 200 |
| **Embeddings OpenAI Small** | `@n8n/n8n-nodes-langchain.embeddingsOpenAi` | LangChain | Generates dense embeddings (`text-embedding-3-small`, 1536 dims) |
| **Store the Docs to Vector DB** | `@n8n/n8n-nodes-langchain.vectorStorePinecone` | Vector Store | Mode: `insert`<br>Pinecone Index: `test-1536` |
| **When chat message received** | `@n8n/n8n-nodes-langchain.chatTrigger` | Trigger | Opens n8n chat UI widget |
| **RAG Agent** | `@n8n/n8n-nodes-langchain.agent` | LangChain Agent | System Message: Answers strictly based on retrieved context and cites source `fileName`. |
| **Brain - gpt-5-mini** | `@n8n/n8n-nodes-langchain.lmChatOpenAi` | LLM | Model: `gpt-4o-mini` / `gpt-5-mini` |
| **Model Chat Memory** | `@n8n/n8n-nodes-langchain.memoryBufferWindow` | Memory | Preserves conversational turn context |
| **Pinecone Vector Store** | `@n8n/n8n-nodes-langchain.vectorStorePinecone` | Tool | Mode: `retrieve-as-tool`<br>`topK`: 3<br>Index: `test-1536` |

---

## ⚙️ Key Agent System Rules

The n8n RAG Agent is configured with the following system instructions:
- **Strict Context Boundary:** Answers questions based **ONLY** on the retrieved documents from Pinecone.
- **Fall-back Message:** If context is missing, responds with: *"I couldn't find that in the uploaded documents."*
- **Source Citation:** Always cites the exact source document name (`fileName`) where the information was found.

---

## 🚀 Getting Started

### Prerequisites
- [n8n](https://n8n.io/) instance running (v1.0+ with LangChain node support).
- **OpenAI API Key** (for embeddings + LLM generation).
- **Pinecone API Key & Index** (Index name: `test-1536` with 1536 dimensions).

### Setup & Import
1. Open your n8n web dashboard.
2. Select **Workflows → Import from File** and upload [`AI3X_Basic_RAG.json`](file:///Users/jaivirsingh/Downloads/AI_WorkFlow_Agents/AI_N8N-RAG/AI3X_Basic_RAG.json).
3. Set up Credentials:
   - **OpenAI Credentials:** Attach your OpenAI API key to `Embeddings OpenAI Small` and `Brain - gpt-5-mini`.
   - **Pinecone Credentials:** Attach your Pinecone API key to both Pinecone nodes (`Store the Docs` and `Pinecone Vector Store`).
4. Activate the Workflow.
5. Upload files via the Form URL to populate Pinecone, then chat with the RAG Agent via the Chat widget.
