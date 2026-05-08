import os

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field

from app.ask import ask
from app.setup import build_retriever
from app.evaluation import run_eval

ARTICLES_PATH = os.getenv(
    "ARTICLES_PATH",
    "data/processed/virusinfektioner_articles.jsonl",
)
EMBED_CACHE_PATH = os.getenv(
    "EMBED_CACHE_PATH",
    "data/cache/chunk_embeddings.npy",
)

retriever = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global retriever

    if os.getenv("SKIP_STARTUP_RETRIEVER") != "1":
        retriever, _, _ = build_retriever(
            articles_path=ARTICLES_PATH,
            cache_path=EMBED_CACHE_PATH,
            max_chars=1200,
            overlap_paragraphs=1,
            alpha=0.5,
        )

    yield

app = FastAPI(
    title="Grounded Medical QA",
    version="0.1.0",
    lifespan=lifespan
)


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int = Field(5, ge=1, le=10)
    mode: str = Field("hybrid")



class EvaluationRequest(BaseModel):
    top_k: int = Field(3, ge=1, le=10)
    mode: str = Field("hybrid")
    limit: int | None = Field(None, ge=1, le=50)

@app.get("/health")
def health():
    return {"status": "ok"}



@app.post("/v1/ask")
def ask_endpoint(req: AskRequest):
    if retriever is None:
        raise HTTPException(status_code=500, detail="Retriever is not initialized")

    try:
        result = ask(
            question=req.question,
            retriever=retriever,
            top_k=req.top_k,
            mode=req.mode,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return result

@app.post("/v1/evaluate")
def evaluate_endpoint(req: EvaluationRequest):
    if retriever is None:
        raise HTTPException(status_code=500, detail="Retriever is not initialized")

    try:
        result = run_eval(
            retriever=retriever,
            top_k=req.top_k,
            mode=req.mode,
            limit=req.limit,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return result

@app.get("/")
def frontend():
    return FileResponse("app/static/index.html")

app.mount("/", StaticFiles(directory="app/static", html=True), name="static")