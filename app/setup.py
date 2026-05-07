import json
from dataclasses import asdict
from pathlib import Path

from app.chunking import build_chunks_from_articles
from app.embed import load_or_create_embeddings
from app.retrieval import ChunkRetriever


def load_articles(jsonl_path: str | Path) -> list[dict]:
    jsonl_path = Path(jsonl_path)

    if not jsonl_path.exists():
        raise FileNotFoundError(f"Article file not found: {jsonl_path}")

    articles = []
    with jsonl_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            articles.append(json.loads(line))

    if not articles:
        raise ValueError(f"No articles loaded from {jsonl_path}")

    return articles


def build_retriever(
    articles_path: str | Path,
    cache_path: str | Path = "data/cache/chunk_embeddings.npy",
    max_chars: int = 1200,
    overlap_paragraphs: int = 1,
    alpha: float = 0.5,
) -> tuple[ChunkRetriever, list[dict], list[dict]]:
    """
    Returns:
        retriever, articles, chunk_dicts
    """
    articles = load_articles(articles_path)

    chunks = build_chunks_from_articles(
        articles=articles,
        max_chars=max_chars,
        overlap_paragraphs=overlap_paragraphs,
        include_title=True,
    )

    chunk_dicts = [asdict(chunk) for chunk in chunks]
    texts = [chunk["text"] for chunk in chunk_dicts]

    embeddings = load_or_create_embeddings(
        texts=texts,
        cache_path=cache_path,
    )

    retriever = ChunkRetriever.from_documents(
        chunks=chunk_dicts,
        chunk_embeddings=embeddings,
        alpha=alpha,
    )

    return retriever, articles, chunk_dicts