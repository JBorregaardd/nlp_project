import os

from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field

from app.ask import ask
from app.setup import build_retriever

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


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(5, ge=1, le=10)
    mode: str = Field("hybrid")



@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/v1/search")
def search_endpoint(req: SearchRequest):
    if retriever is None:
        raise HTTPException(status_code=500, detail="Retriever is not initialized")

    try:
        results = retriever.search(
            query=req.query,
            top_k=req.top_k,
            mode=req.mode,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "query": req.query,
        "mode": req.mode,
        "results": results,
    }


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