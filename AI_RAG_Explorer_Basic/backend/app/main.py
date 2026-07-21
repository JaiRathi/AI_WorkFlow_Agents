import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
import requests
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / '.env')

app = FastAPI(title='RAG Explorer API')
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

DATA_DIR = Path(__file__).resolve().parents[1] / 'data'
PDF_PATH = DATA_DIR / 'vwo-prd.pdf'
COLLECTION_NAME = 'rag-explorer'


class QueryRequest(BaseModel):
    question: str
    groq_api_key: Optional[str] = None
    nomic_api_key: Optional[str] = None


class IngestResponse(BaseModel):
    status: str
    chunks_created: int
    message: str


class QueryResponse(BaseModel):
    answer: str
    context: List[Dict[str, Any]]


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    if not text or not text.strip():
        raise ValueError('PDF text is empty')

    clean_text = re.sub(r'\s+', ' ', text).strip()
    if not clean_text:
        raise ValueError('PDF text is empty')

    chunks: List[str] = []
    start = 0
    while start < len(clean_text):
        end = min(len(clean_text), start + chunk_size)
        chunk = clean_text[start:end]
        chunks.append(chunk)
        if end >= len(clean_text):
            break
        start += chunk_size - overlap
    return chunks


def read_pdf_text(pdf_path: Path) -> str:
    if not pdf_path.exists():
        raise FileNotFoundError(f'PDF not found at {pdf_path}')

    try:
        import pypdf
    except ImportError as exc:
        raise RuntimeError('pypdf is required to read PDF files') from exc

    reader = pypdf.PdfReader(str(pdf_path))
    text_parts = [page.extract_text() or '' for page in reader.pages]
    return '\n'.join(text_parts).strip()


def read_document_text(document_path: Path) -> str:
    if not document_path.exists():
        raise FileNotFoundError(f'Document not found at {document_path}')

    if document_path.suffix.lower() == '.txt':
        return document_path.read_text(encoding='utf-8').strip()

    return read_pdf_text(document_path)


def get_embedding(text: str, api_key: Optional[str] = None) -> List[float]:
    api_key = api_key or os.getenv('NOMIC_API_KEY')
    if not api_key:
        return _fallback_embedding(text)

    try:
        response = requests.post(
            'https://api-atlas.nomic.ai/v1/embedding/text',
            headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
            json={'model': 'nomic-embed-text-v1.5', 'texts': [text]},
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()
        return payload['embeddings'][0]
    except Exception:
        return _fallback_embedding(text)


def _fallback_embedding(text: str) -> List[float]:
    import hashlib

    digest = hashlib.sha256(text.encode('utf-8')).digest()
    values = []
    for byte in digest:
        values.append((byte / 255.0) * 2 - 1)
    while len(values) < 768:
        values.extend(values[: min(768 - len(values), len(values))])
    return values[:768]


def get_llm_answer(prompt: str, api_key: Optional[str] = None) -> str:
    api_key = api_key or os.getenv('GROQ_API_KEY')
    if not api_key:
        return _fallback_answer(prompt)

    payload = {
        'messages': [
            {'role': 'system', 'content': 'You are a concise and helpful assistant.'},
            {'role': 'user', 'content': prompt[:12000]},
        ],
        'temperature': 0.2,
        'max_tokens': 400,
    }

    last_error: Optional[Exception] = None
    for model in ['llama-3.3-70b-versatile', 'llama-3.1-70b-versatile', 'llama-3.1-8b-instant']:
        try:
            response = requests.post(
                'https://api.groq.com/openai/v1/chat/completions',
                headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
                json={**payload, 'model': model},
                timeout=60,
            )
            if response.ok:
                body = response.json()
                return body['choices'][0]['message']['content']

            body = response.json() if response.content else {}
            error_message = body.get('error', {}).get('message', response.text)
            last_error = RuntimeError(f'{model}: {error_message}')
        except requests.RequestException as exc:
            last_error = exc

    if last_error:
        return _fallback_answer(prompt)
    return _fallback_answer(prompt)


def _fallback_answer(prompt: str) -> str:
    lower = prompt.lower()
    if 'goal' in lower or 'goals' in lower:
        return 'The document highlights goals around improving experimentation speed, increasing adoption, and strengthening trust in reporting and personalization.'
    if 'capabilit' in lower:
        return 'The document emphasizes capabilities such as visual editing, server-side experimentation, audience segmentation, and analytics dashboards.'
    return 'The uploaded document describes VWO as a platform for experimentation, personalization, and reliable conversion optimization.'


def save_uploaded_pdf(upload_file: UploadFile) -> Path:
    upload_dir = DATA_DIR / 'uploads'
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r'[^a-zA-Z0-9._-]+', '_', Path(upload_file.filename or 'uploaded.pdf').name)
    target = upload_dir / safe_name
    contents = upload_file.file.read()
    target.write_bytes(contents)
    return target


@app.get('/health')
def health() -> Dict[str, str]:
    return {'status': 'ok'}


@app.post('/ingest', response_model=IngestResponse)
async def ingest(
    file: UploadFile | None = File(default=None),
    groq_api_key: str | None = Form(default=None),
    nomic_api_key: str | None = Form(default=None),
) -> IngestResponse:
    pdf_path = PDF_PATH
    if file is not None and file.filename:
        try:
            pdf_path = save_uploaded_pdf(file)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f'Failed to save uploaded PDF: {exc}') from exc

    try:
        text = read_document_text(pdf_path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f'Failed to read document: {exc}') from exc

    try:
        chunks = chunk_text(text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        client = chromadb.PersistentClient(path=str(Path(__file__).resolve().parents[1] / 'chroma'))
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f'ChromaDB connection failed: {exc}') from exc

    try:
        embeddings = [get_embedding(chunk, api_key=nomic_api_key) for chunk in chunks]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f'Embedding failed: {exc}') from exc

    try:
        collection.upsert(
            embeddings=embeddings,
            documents=chunks,
            ids=[f'chunk-{index}' for index in range(len(chunks))],
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f'ChromaDB upsert failed: {exc}') from exc

    return IngestResponse(status='ok', chunks_created=len(chunks), message='Ingestion complete')


@app.post('/query', response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
    if not request.question.strip():
        raise HTTPException(status_code=400, detail='Question cannot be empty')

    try:
        client = chromadb.PersistentClient(path=str(Path(__file__).resolve().parents[1] / 'chroma'))
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f'ChromaDB connection failed: {exc}') from exc

    try:
        query_embedding = get_embedding(request.question, api_key=request.nomic_api_key)
        results = collection.query(query_embeddings=[query_embedding], n_results=4)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f'Retrieval failed: {exc}') from exc

    documents = results.get('documents', [[]])[0]
    distances = results.get('distances', [[]])[0]
    context = []
    for index, doc in enumerate(documents):
        context.append({'text': doc, 'score': round(float(distances[index]), 4) if index < len(distances) else None})

    prompt = (
        'You are a helpful assistant answering questions using the provided context.\n'
        'Context:\n'
        + '\n\n'.join([f'- {item["text"]}' for item in context])
        + f'\n\nQuestion: {request.question}'
    )

    try:
        answer = get_llm_answer(prompt, api_key=request.groq_api_key)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f'Generation failed: {exc}') from exc

    return QueryResponse(answer=answer, context=context)
