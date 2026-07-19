from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes.ask import router as ask_router
from src.api.routes.ingest import router as ingest_router
from src.api.routes.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[QABuddy] Starting up...")
    yield
    print("[QABuddy] Shutting down...")


app = FastAPI(
    title="QABuddy.ai",
    description="Hybrid RAG system for QA engineers — answers grounded in your code, test cases, JIRA tickets, and docs.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ask_router)
app.include_router(ingest_router)
app.include_router(health_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
