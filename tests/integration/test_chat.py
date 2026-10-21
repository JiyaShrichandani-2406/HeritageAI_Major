from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.api.v1.endpoints import chat as chat_endpoint


client = TestClient(app)


def sample_answer():
    """Return a predictable response for integration tests."""
    return {
        "answer": "The Taj Mahal is located in Agra, Uttar Pradesh, India.",
        "sources": [
            {
                "title": "Taj Mahal",
                "url": "https://example.org/test/taj-mahal",
                "relevance_score": 0.85,
            }
        ],
        "grounded": True,
        "message": "Test response generated from mocked context.",
    }


def test_chat_endpoint_success(monkeypatch):
    """A valid request should return the expected response structure."""

    def mock_generate_answer(question, top_k=3):
        assert question == "Where is the Taj Mahal located?"
        assert top_k == 3
        return sample_answer()

    monkeypatch.setattr(
        chat_endpoint,
        "generate_answer",
        mock_generate_answer,
    )

    response = client.post(
        "/api/v1/chat",
        json={
            "question": "Where is the Taj Mahal located?",
            "session_id": None,
            "top_k": 3,
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["answer"] == sample_answer()["answer"]
    assert len(data["sources"]) == 1
    assert data["sources"][0]["title"] == "Taj Mahal"
    assert data["grounded"] is True
    assert "message" in data


def test_chat_endpoint_rejects_empty_question():
    """An empty question should fail request validation."""

    response = client.post(
        "/api/v1/chat",
        json={
            "question": "",
            "session_id": None,
            "top_k": 3,
        },
    )

    assert response.status_code == 422


def test_chat_endpoint_rejects_invalid_top_k():
    """A top_k value outside the schema limits should be rejected."""

    response = client.post(
        "/api/v1/chat",
        json={
            "question": "Tell me about Indian heritage.",
            "session_id": None,
            "top_k": 0,
        },
    )

    assert response.status_code == 422


def test_chat_endpoint_rejects_top_k_above_maximum():
    response = client.post(
        "/api/v1/chat",
        json={
            "question": "Tell me about Indian heritage.",
            "top_k": 11,
        },
    )

    assert response.status_code == 422


def test_chat_endpoint_rejects_question_longer_than_2000_characters():
    response = client.post(
        "/api/v1/chat",
        json={"question": "a" * 2001},
    )

    assert response.status_code == 422


def test_chat_endpoint_returns_bad_request_for_whitespace_question():
    response = client.post(
        "/api/v1/chat",
        json={"question": "   "},
    )

    assert response.status_code == 400


def test_chat_endpoint_handles_service_unavailable(monkeypatch):
    """A runtime failure should return HTTP 503."""

    def mock_generate_answer(question, top_k=3):
        raise RuntimeError("Simulated model service failure")

    monkeypatch.setattr(
        chat_endpoint,
        "generate_answer",
        mock_generate_answer,
    )

    response = client.post(
        "/api/v1/chat",
        json={"question": "Tell me about Indian heritage."},
    )

    assert response.status_code == 503
    assert "currently unavailable" in response.json()["detail"]


def test_chat_endpoint_handles_ollama_timeout(monkeypatch):
    def mock_generate_answer(question, top_k=3):
        raise RuntimeError("The Ollama request timed out.")

    monkeypatch.setattr(
        chat_endpoint,
        "generate_answer",
        mock_generate_answer,
    )

    response = client.post(
        "/api/v1/chat",
        json={"question": "Tell me about Indian heritage."},
    )

    assert response.status_code == 503