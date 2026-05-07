import pytest

from app.retrieval import ChunkRetriever


def example_chunks():
    return [
        {
            "chunk_id": "c1",
            "article_title": "Forkølelse",
            "url": "https://example.com/forkolelse",
            "text": "Forkølelse giver hoste, løbende næse og ondt i halsen.",
        },
        {
            "chunk_id": "c2",
            "article_title": "Influenza",
            "url": "https://example.com/influenza",
            "text": "Influenza giver ofte feber, muskelsmerter og træthed.",
        },
        {
            "chunk_id": "c3",
            "article_title": "Norovirus",
            "url": "https://example.com/norovirus",
            "text": "Norovirus giver typisk opkast, kvalme og diarré.",
        },
    ]


def test_sparse_retrieval_returns_relevant_chunk():
    retriever = ChunkRetriever.from_documents(example_chunks())

    results = retriever.search(
        query="hoste og løbende næse",
        top_k=1,
        mode="sparse",
    )

    assert len(results) == 1
    assert results[0]["title"] == "Forkølelse"


def test_unknown_retrieval_mode_raises_value_error():
    retriever = ChunkRetriever.from_documents(example_chunks())

    with pytest.raises(ValueError, match="Unknown retrieval mode"):
        retriever.search(
            query="hoste",
            mode="invalid_mode",
        )