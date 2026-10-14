from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.api.v1.router import api_router
from backend.app.core.config import get_settings

app = FastAPI()
app.include_router(api_router)
client = TestClient(app)


def test_health_returns_the_agreed_fields():
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert set(response.json()) == {"status", "service", "version"}


def test_health_values_come_from_settings():
    settings = get_settings()

    response = client.get("/api/v1/health")

    assert response.json() == {
        "status": "ok",
        "service": settings.service_name,
        "version": settings.app_version,
    }


def test_health_is_only_available_under_the_versioned_prefix():
    assert client.get("/health").status_code == 404


def test_health_does_not_accept_post():
    assert client.post("/api/v1/health").status_code == 405