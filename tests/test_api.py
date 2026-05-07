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


def test_search_endpoint_returns_results(monkeypatch):
    monkeypatch.setattr(main_module, "retriever", FakeRetriever())

    client = TestClient(main_module.app)

    response = client.post(
        "/v1/search",
        json={
            "query": "hoste og løbende næse",
            "top_k": 1,
            "mode": "hybrid",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["query"] == "hoste og løbende næse"
    assert data["mode"] == "hybrid"
    assert len(data["results"]) == 1
    assert data["results"][0]["title"] == "Forkølelse"