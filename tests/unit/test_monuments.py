from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.api.v1.endpoints.monuments import router
from backend.app.services.heritage_service import get_heritage_context

# A small app with only this router, so the test does not depend on other modules.
app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_taj_mahal_returns_details_and_sources():
    response = client.get("/api/v1/monuments/taj-mahal")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Taj Mahal"
    assert data["city"] == "Agra"
    assert data["history"]
    assert len(data["sources"]) >= 1
    assert data["sources"][0]["url"].startswith("https://")


def test_monument_id_is_case_insensitive():
    response = client.get("/api/v1/monuments/TAJ-MAHAL")

    assert response.status_code == 200


def test_unknown_monument_returns_404():
    response = client.get("/api/v1/monuments/does-not-exist")

    assert response.status_code == 404


def test_heritage_context_contains_history_and_sources():
    context = get_heritage_context("Taj Mahal")

    assert "Taj Mahal" in context
    assert "History:" in context
    assert "https://" in context


def test_heritage_context_is_empty_for_unknown_destination():
    assert get_heritage_context("Unknown Place") == ""
