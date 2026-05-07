import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from app.embed import embed_query


class ChunkRetriever:
    def __init__(
        self,
        chunks,
        chunk_embeddings=None,
        tfidf_vectorizer=None,
        tfidf_matrix=None,
        alpha=0.5,
    ):
        self.chunks = chunks
        self.chunk_embeddings = chunk_embeddings
        self.tfidf_vectorizer = tfidf_vectorizer
        self.tfidf_matrix = tfidf_matrix
        self.alpha = alpha

        self.chunk_id_to_index = {
            chunk["chunk_id"]: i for i, chunk in enumerate(chunks)
        }

    @classmethod
    def from_documents(cls, chunks, chunk_embeddings=None, alpha=0.5):
        texts = [chunk["text"] for chunk in chunks]

        tfidf_vectorizer = TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 2),
            # stop_words=None is safer for Danish
        )
        tfidf_matrix = tfidf_vectorizer.fit_transform(texts)

        return cls(
            chunks=chunks,
            chunk_embeddings=chunk_embeddings,
            tfidf_vectorizer=tfidf_vectorizer,
            tfidf_matrix=tfidf_matrix,
            alpha=alpha,
        )

    def _format_results(self, scores, top_k=5):
        top_idx = np.argsort(scores)[-top_k:][::-1]

        results = []
        for i in top_idx:
            chunk = self.chunks[i]
            results.append({
                "chunk_id": chunk["chunk_id"],
                "title": chunk.get("article_title", ""),
                "url": chunk.get("url", ""),
                "score": float(scores[i]),
                "text": chunk["text"],
            })
        return results

    def _dense_scores(self, query):
        if self.chunk_embeddings is None:
            raise ValueError("Dense retrieval is not available")

        query_emb = embed_query(query)
        scores = self.chunk_embeddings @ query_emb
        return scores

    def _sparse_scores(self, query):
        if self.tfidf_vectorizer is None or self.tfidf_matrix is None:
            raise ValueError("Sparse retrieval is not available")

        query_vec = self.tfidf_vectorizer.transform([query])
        scores = (self.tfidf_matrix @ query_vec.T).toarray().ravel()
        return scores

    def _minmax_normalize(self, scores):
        scores = np.asarray(scores, dtype=np.float32)
        min_score = scores.min()
        max_score = scores.max()

        if max_score - min_score < 1e-12:
            return np.zeros_like(scores)

        return (scores - min_score) / (max_score - min_score)

    def search(self, query, top_k=5, mode="dense"):
        mode = mode.lower()

        if mode == "dense":
            scores = self._dense_scores(query)

        elif mode == "sparse":
            scores = self._sparse_scores(query)

        elif mode == "hybrid":
            dense_scores = self._dense_scores(query)
            sparse_scores = self._sparse_scores(query)

            dense_scores = self._minmax_normalize(dense_scores)
            sparse_scores = self._minmax_normalize(sparse_scores)

            scores = self.alpha * dense_scores + (1 - self.alpha) * sparse_scores

        else:
            raise ValueError(f"Unknown retrieval mode: {mode}")

        return self._format_results(scores, top_k=top_k)

    def similar_chunks(self, chunk_id, top_k=5):
        if self.chunk_embeddings is None:
            raise ValueError("Dense retrieval is required for similar chunk search")

        if chunk_id not in self.chunk_id_to_index:
            raise ValueError(f"Unknown chunk_id: {chunk_id}")

        idx = self.chunk_id_to_index[chunk_id]
        chunk_emb = self.chunk_embeddings[idx]

        scores = self.chunk_embeddings @ chunk_emb

        top_idx = np.argsort(scores)[-(top_k + 1):][::-1]
        top_idx = [i for i in top_idx if i != idx][:top_k]

        results = []
        for i in top_idx:
            chunk = self.chunks[i]
            results.append({
                "chunk_id": chunk["chunk_id"],
                "title": chunk.get("article_title", ""),
                "url": chunk.get("url", ""),
                "score": float(scores[i]),
                "text": chunk["text"],
            })

        return results

    def get_chunks_by_ids(self, chunk_ids):
        result = []
        for chunk_id in chunk_ids:
            idx = self.chunk_id_to_index.get(chunk_id)
            if idx is not None:
                result.append(self.chunks[idx])
        return result
    
    