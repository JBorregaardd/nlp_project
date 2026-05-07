import os
from pathlib import Path
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("CAMPUSAI_API_KEY")
base_url = os.getenv("CAMPUSAI_API_URL")
embed_model = os.getenv("CAMPUSAI_EMBED_MODEL")

if not api_key:
    raise ValueError("Missing CAMPUSAI_API_KEY")
if not base_url:
    raise ValueError("Missing CAMPUSAI_API_URL")
if not embed_model:
    raise ValueError("Missing CAMPUSAI_EMBED_MODEL")


client = OpenAI(
    api_key=api_key,
    base_url=base_url,
)

def l2_normalize(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms = np.clip(norms, 1e-12, None)
    return vectors / norms


def embed_texts(texts, model=embed_model, batch_size=64, normalize=True):
    if not texts:
        return np.empty((0, 0), dtype=np.float32)

    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]

        response = client.embeddings.create(
            model=model,
            input=batch
        )

        batch_embeddings = [item.embedding for item in response.data]
        all_embeddings.extend(batch_embeddings)

    embeddings = np.asarray(all_embeddings, dtype=np.float32)

    if normalize:
        embeddings = l2_normalize(embeddings)

    return embeddings


def embed_query(text, model=embed_model, normalize=True):
    embedding = embed_texts([text], model=model, batch_size=64, normalize=normalize)
    return embedding[0]


def load_or_create_embeddings(texts, cache_path, model=embed_model, batch_size=64, normalize=True):
    cache_path = Path(cache_path)

    if cache_path.exists():
        embeddings = np.load(cache_path)
        return embeddings.astype(np.float32)

    print(f"Computing embeddings and saving to {cache_path}")
    embeddings = embed_texts(
        texts=texts,
        model=model,
        batch_size=batch_size,
        normalize=normalize,
    )

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(cache_path, embeddings)

    return embeddings