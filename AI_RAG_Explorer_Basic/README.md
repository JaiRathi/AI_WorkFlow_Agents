# RAG Explorer

A full-stack RAG demo built with React, Vite, FastAPI, ChromaDB, and Groq/Nomic APIs.

## What it does

- Ingests a local PDF from the backend data folder.
- Splits the text into fixed-size chunks with overlap.
- Generates embeddings with the Nomic embedding endpoint.
- Stores the chunks in a local ChromaDB collection.
- Runs a retrieval-augmented query and displays the top 4 context chunks plus the generated answer.

## Prerequisites

- Python 3.10+
- Node.js 20+
- A Groq API key
- A Nomic API key

## Backend setup

1. Create a virtual environment:
   ```bash
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the backend folder with:
   ```env
   GROQ_API_KEY=your_groq_key
   NOMIC_API_KEY=your_nomic_key
   ```
4. Place your PDF at `backend/data/vwo-prd.pdf`.
5. Start the API server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

## Frontend setup

1. Install frontend dependencies:
   ```bash
   npm install
   ```
2. Start the Vite dev server:
   ```bash
   npm run dev
   ```
3. Open the Vite URL displayed in the terminal.

## ChromaDB

This project uses ChromaDB in persistent local mode. The database is stored in the `backend/chroma` directory.

## Notes

- If the API keys are missing, ingestion and query will fail with a clear error response.
- If the PDF is empty or missing, the backend returns a descriptive error.
- If ChromaDB cannot be initialized, the API returns a connection failure message.
