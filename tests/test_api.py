from fastapi.testclient import TestClient

import app.main as main_module


class FakeRetriever:
    def search(self, query, top_k=5, mode="hybrid"):
        return [
            {
                "chunk_id": "c1",
                "title": "Forkølelse",
                "url": "https://example.com/forkolelse",
                "score": 0.95,
                "text": "Forkølelse giver hoste og løbende næse.",
            }
        ]


def test_health_endpoint():
    client = TestClient(main_module.app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ask_endpoint():
    client = TestClient(main_module.app)

    # Patch the retriever with our fake retriever
    main_module.retriever = FakeRetriever()

    response = client.post(
        "/v1/ask",
        json={
            "question": "Hvad er forkølelse?",
            "top_k": 3,
            "mode": "hybrid",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data