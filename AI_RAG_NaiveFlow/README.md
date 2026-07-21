# 🛒 AI 3X Naive RAG (E-Commerce Test Cases)

A Naive **Retrieval-Augmented Generation (RAG)** pipeline built in **Langflow**. It ingests e-commerce test case repositories (CSV, PDF, TXT), splits text into chunked documents, embeds text using **Mistral AI (`mistral-embed`)**, indexes chunks in a local **Chroma DB** instance, and executes contextual retrieval with **Groq (`llama-3.3-70b-versatile`)**.

---

## 📐 Workflow Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ INGESTION PIPELINE                                                                          │
│                                                                                             │
│  ┌───────────────────────┐      ┌─────────────────────────┐      ┌───────────────────────┐  │
│  │       Read File       │ ───> │       Split Text        │ ───> │       Chroma DB       │  │
│  │ (CSV / PDF / TXT)     │      │ (Size: 1000, Overlap:200)│      │  (Collection: test)   │  │
│  └───────────────────────┘      └─────────────────────────┘      └───────────▲───────────┘  │
│                                                                              │              │
│                                                                  ┌───────────┴──────────┐   │
│                                                                  │ Mistral AI Embeddings│   │
│                                                                  │   (mistral-embed)    │   │
│                                                                  └──────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ RETRIEVAL & QA PIPELINE                                                                    │
│                                                                                             │
│  ┌───────────────────────┐               ┌───────────────────────┐      ┌────────────────┐  │
│  │      Chat Input       │ ────────────> │    Prompt Template    │ ───> │  Groq LLM      │  │
│  │ (User Question)       │               │ (Context + Question)  │      │(llama-3.3-70b) │  │
│  └───────────────────────┘               └───────────▲───────────┘      └───────┬────────┘  │
│                                                      │                          │           │
│                                          ┌───────────┴───────────┐              │           │
│                                          │    Parser Component   │              │           │
│                                          └───────────▲───────────┘              │           │
│                                                      │                          ▼           │
│                                          ┌───────────┴───────────┐      ┌────────────────┐  │
│                                          │  Chroma DB Retrieval  │      │  Chat Output   │  │
│                                          │ (Similarity/MMR, k=20)│      │ (Final Answer) │  │
│                                          └───────────────────────┘      └────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🧩 Component Breakdown

| Node Name | Node Type | Component Class | Parameters & Configurations |
| :--- | :--- | :--- | :--- |
| **Read File** | `File` | Custom File Component | Loads test case repository document (CSV/PDF/TXT) |
| **Split Text** | `SplitText` | `langchain_text_splitters` | `chunk_size`: 1000<br>`chunk_overlap`: 200 |
| **MistralAI Embeddings (Ingest)** | `MistalAIEmbeddings` | `langchain_mistralai` | Model: `mistral-embed`<br>Max retries: 5<br>Timeout: 120s |
| **Chroma DB (Ingest)** | `Chroma` | `langchain_chroma` | Persist directory: `./chroma_db`<br>Collection: `test` |
| **Chroma DB (Search)** | `Chroma` | `langchain_chroma` | `search_type`: `Similarity` / `MMR`<br>`number_of_results`: 20 |
| **Parser** | `ParserComponent` | Custom Component | Formats retrieved chunks into uniform text context |
| **Chat Input** | `ChatInput` | Built-in | Accepts user queries regarding e-commerce test suites |
| **Prompt Template** | `PromptTemplate` | Built-in | Constructs context-bounded RAG prompt |
| **Groq Model** | `GroqModel` | Built-in | **Model:** `llama-3.3-70b-versatile`<br>**Temperature:** `0.1` |
| **Chat Output** | `ChatOutput` | Built-in | Displays QA response in chat window |

---

## 🔒 Guardrails & Prompt System Rules

- **Strict Grounding:** The Groq LLM system message strictly restricts responses to information present inside retrieved Chroma DB chunks.
- **Fall-back Behavior:** If no relevant test case matches the query context, the LLM refrains from hallucinating or introducing external domain knowledge.
- **Coverage:** Designed specifically for querying e-commerce test scenarios (Checkout, Cart, Payment Gateways, User Auth, Search/Filter tests).

---

## 🚀 Getting Started

### Prerequisites
- [Langflow](https://github.com/langflow-ai/langflow) framework.
- **Mistral AI API Key** (for `mistral-embed`).
- **Groq API Key** (for `llama-3.3-70b-versatile`).

### Setup & Execution
1. Open Langflow and click **Import Flow**.
2. Select [`AI_3X_Naive RAG_Task11July2026.json`](file:///Users/jaivirsingh/Downloads/AI_WorkFlow_Agents/AI_RAG_NaiveFlow/AI_3X_Naive%20RAG_Task11July2026.json).
3. Set your API Keys:
   - Mistral API key in **MistralAI Embeddings** node.
   - Groq API key in **Groq** node.
4. Upload your e-commerce test cases CSV/PDF file to the **Read File** node.
5. Trigger ingestion, then ask questions in the Playground chat (e.g. *"What test cases cover payment gateway failure scenarios?"*).
