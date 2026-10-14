from fastapi.testclient import TestClient

from backend.app.core.config import get_settings
from backend.app.main import app


def test_main_app_uses_configured_metadata():
    settings = get_settings()

    assert app.title == settings.app_name
    assert app.version == settings.app_version


def test_main_app_root_endpoint():
    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Welcome to HeritageAI API",
        "status": "running",
    }


def test_main_app_versioned_health_endpoint():
    settings = get_settings()

    with TestClient(app) as client:
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": settings.service_name,
        "version": settings.app_version,
    }


def test_main_app_registers_chat_and_itinerary_routes():
    paths = app.openapi()["paths"]

    assert "/api/v1/chat" in paths
    assert "/api/v1/itinerary" in paths


def test_main_app_configures_cors_middleware():
    settings = get_settings()
    origins = list(settings.cors_origins)

    assert origins
    assert any(
        middleware.cls.__name__ == "CORSMiddleware"
        for middleware in app.user_middleware
    )

    with TestClient(app) as client:
        response = client.options(
            "/api/v1/health",
            headers={
                "Origin": origins[0],
                "Access-Control-Request-Method": "GET",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origins[0]
