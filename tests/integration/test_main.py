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


def test_openapi_documents_itinerary_error_shapes_and_status_codes():
    paths = app.openapi()["paths"]
    responses = paths["/api/v1/itinerary"]["post"]["responses"]

    assert {"200", "422", "500", "502", "503"} <= responses.keys()
    validation_example = responses["422"]["content"]["application/json"]["example"]
    assert isinstance(validation_example["detail"], list)

    ai_error = responses["502"]["content"]["application/json"]["example"]
    assert isinstance(ai_error["detail"], str)
    assert {"400", "422", "500", "503"} <= paths["/api/v1/chat"]["post"][
        "responses"
    ].keys()
    assert {"404", "500", "503"} <= paths[
        "/api/v1/monuments/{monument_id}"
    ]["get"]["responses"].keys()
    assert {"422", "500", "503"} <= paths["/api/v1/places/nearby"]["get"][
        "responses"
    ].keys()
    assert {"422", "500", "503"} <= paths["/api/v1/routes"]["post"][
        "responses"
    ].keys()
    assert {"422", "500", "503"} <= paths["/api/v1/services"]["get"][
        "responses"
    ].keys()


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
