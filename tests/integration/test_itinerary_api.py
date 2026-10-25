
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.api.v1.endpoints import itinerary as itinerary_endpoint


client = TestClient(app)


@pytest.fixture
def mock_generated_itinerary(monkeypatch):
    def fake_generate_itinerary(request):
        return {
            "itinerary": [
                {
                    "title": "Day 1 - Heritage",
                    "activities": [
                        {
                            "place_name": "Historical Site A",
                            "description": "Explore local heritage.",
                            "estimated_entry_cost": 100,
                            "estimated_transport_cost": 50,
                            "estimated_food_cost": 150,
                            "source_url": None,
                        }
                    ],
                },
                {
                    "title": "Day 2 - Architecture",
                    "activities": [
                        {
                            "place_name": "Historical Site B",
                            "description": "Explore local architecture.",
                            "estimated_entry_cost": 200,
                            "estimated_transport_cost": 100,
                            "estimated_food_cost": 200,
                            "source_url": None,
                        }
                    ],
                },
            ],
            "assumptions": ["Costs are sample estimates."],
            "transport_options": [
                {
                    "id": "delhi-bhopal-train",
                    "origin": "Delhi",
                    "destination": "Bhopal",
                    "transport_type": "train",
                    "estimated_cost": 500,
                    "currency": "INR",
                    "estimated_duration_minutes": 120,
                    "cost_status": "estimated",
                    "source_url": "https://example.com/train",
                    "notes": "",
                }
            ],
            "visitor_services": [
                {
                    "id": "bhopal-guide",
                    "name": "Bhopal guide",
                    "category": "guide",
                    "location": "Bhopal",
                    "latitude": None,
                    "longitude": None,
                    "description": "Local guide service",
                    "estimated_cost": 1000,
                    "currency": "INR",
                    "cost_status": "estimated",
                    "source_url": "https://example.com/guide",
                }
            ],
        }

    monkeypatch.setattr(
        itinerary_endpoint,
        "generate_itinerary",
        fake_generate_itinerary,
    )


def test_create_itinerary_success(mock_generated_itinerary):
    response = client.post(
        "/api/v1/itinerary",
        json={
            "destination": "Bhopal",
            "origin": "Delhi",
            "budget": 3000,
            "days": 2,
            "interests": ["history"],
            "travelers": 1,
            "travel_style": "budget",
            "include_food": True,
            "include_transport": True,
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["destination"] == "Bhopal"
    assert data["days"] == 2
    assert len(data["itinerary"]) == 2
    assert data["estimated_total_cost"] == 800
    assert data["within_budget"] is None
    assert data["remaining_budget"] is None
    assert data["known_cost_subtotal"] == 0
    assert data["transport_options"][0]["id"] == "delhi-bhopal-train"
    assert data["visitor_services"][0]["id"] == "bhopal-guide"
    assert data["estimated_total_cost"] == 800
    assert any(
        "not included in the itinerary total" in assumption
        for assumption in data["assumptions"]
    )


def test_create_itinerary_invalid_budget():
    response = client.post(
        "/api/v1/itinerary",
        json={
            "destination": "Bhopal",
            "budget": 0,
            "days": 2,
        },
    )

    assert response.status_code == 422


def test_create_itinerary_rejects_negative_budget():
    response = client.post(
        "/api/v1/itinerary",
        json={
            "destination": "Bhopal",
            "budget": -1,
            "days": 2,
        },
    )

    assert response.status_code == 422


def test_create_itinerary_invalid_days():
    response = client.post(
        "/api/v1/itinerary",
        json={
            "destination": "Bhopal",
            "budget": 3000,
            "days": 0,
        },
    )

    assert response.status_code == 422


def test_create_itinerary_rejects_more_than_30_days():
    response = client.post(
        "/api/v1/itinerary",
        json={
            "destination": "Bhopal",
            "budget": 3000,
            "days": 31,
        },
    )

    assert response.status_code == 422


def test_create_itinerary_missing_destination():
    response = client.post(
        "/api/v1/itinerary",
        json={
            "budget": 3000,
            "days": 2,
        },
    )

    assert response.status_code == 422


@pytest.mark.parametrize("destination", ["", "A", "   "])
def test_create_itinerary_rejects_missing_or_short_destination(destination):
    response = client.post(
        "/api/v1/itinerary",
        json={
            "destination": destination,
            "budget": 3000,
            "days": 2,
        },
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "extra",
    [
        {"travel_style": "luxury"},
        {"hotel": "Palace"},
    ],
)
def test_create_itinerary_rejects_unsupported_or_extra_fields(extra):
    response = client.post(
        "/api/v1/itinerary",
        json={
            "destination": "Bhopal",
            "budget": 3000,
            "days": 2,
            **extra,
        },
    )

    assert response.status_code == 422


def test_create_itinerary_ai_service_unavailable(monkeypatch):
    def fake_generate_itinerary(request):
        raise RuntimeError("Simulated AI service failure.")

    monkeypatch.setattr(
        itinerary_endpoint,
        "generate_itinerary",
        fake_generate_itinerary,
    )

    response = client.post(
        "/api/v1/itinerary",
        json={
            "destination": "Bhopal",
            "budget": 3000,
            "days": 2,
        },
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Simulated AI service failure."


def test_create_itinerary_ollama_timeout_returns_gateway_timeout(monkeypatch):
    from backend.app.ai.llm_client import OllamaTimeoutError

    def timeout(request):
        raise OllamaTimeoutError("Ollama timed out generating the itinerary.")

    monkeypatch.setattr(
        itinerary_endpoint,
        "generate_itinerary",
        timeout,
    )

    response = client.post(
        "/api/v1/itinerary",
        json={
            "destination": "Agra",
            "budget": 5000,
            "days": 1,
        },
    )

    assert response.status_code == 504
    assert response.json()["detail"] == (
        "Ollama timed out generating the itinerary."
    )


def test_create_itinerary_reports_unsupported_destination(monkeypatch):
    def unsupported_destination(request):
        from backend.app.ai.itinerary_generator import (
            UnsupportedDestinationError,
        )

        raise UnsupportedDestinationError(
            "No heritage or nearby-place data is available for Bhopal."
        )

    monkeypatch.setattr(
        itinerary_endpoint,
        "generate_itinerary",
        unsupported_destination,
    )

    response = client.post(
        "/api/v1/itinerary",
        json={"destination": "Bhopal", "budget": 3000, "days": 1},
    )

    assert response.status_code == 422
    assert "No heritage or nearby-place data" in response.json()["detail"]


def test_create_itinerary_rejects_empty_day_from_generator(monkeypatch):
    def fake_generate_itinerary(request):
        return {
            "itinerary": [
                {
                    "title": "Day 1",
                    "activities": [
                        {
                            "place_name": "Site A",
                            "description": "Explore the heritage site.",
                            "estimated_entry_cost": 100,
                        }
                    ],
                },
                {"title": "Day 2", "activities": []},
            ],
            "assumptions": [],
        }

    monkeypatch.setattr(
        itinerary_endpoint,
        "generate_itinerary",
        fake_generate_itinerary,
    )

    response = client.post(
        "/api/v1/itinerary",
        json={"destination": "Agra", "budget": 3000, "days": 2},
    )

    assert response.status_code == 502
    assert "Each itinerary day must contain at least one activity" in (
        response.json()["detail"]
    )


def test_create_itinerary_rejects_wrong_number_of_days_from_generator(
    monkeypatch,
):
    monkeypatch.setattr(
        itinerary_endpoint,
        "generate_itinerary",
        lambda request: {"itinerary": [], "assumptions": []},
    )

    response = client.post(
        "/api/v1/itinerary",
        json={"destination": "Agra", "budget": 3000, "days": 1},
    )

    assert response.status_code == 502
    assert "Expected 1 daily plans" in response.json()["detail"]


def test_create_itinerary_returns_null_total_for_unknown_costs(monkeypatch):
    def fake_generate_itinerary(request):
        return {
            "itinerary": [
                {
                    "title": "Day 1",
                    "activities": [
                        {
                            "place_name": "Site A",
                            "description": "Explore the heritage site.",
                            "estimated_entry_cost": None,
                            "entry_cost_status": "unknown",
                            "estimated_transport_cost": None,
                            "transport_cost_status": "unknown",
                            "estimated_food_cost": None,
                            "food_cost_status": "unknown",
                        }
                    ],
                }
            ],
            "assumptions": [],
        }

    monkeypatch.setattr(
        itinerary_endpoint,
        "generate_itinerary",
        fake_generate_itinerary,
    )

    response = client.post(
        "/api/v1/itinerary",
        json={"destination": "Agra", "budget": 3000, "days": 1},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["known_cost_subtotal"] == 0
    assert data["estimated_total_cost"] is None
    assert data["remaining_budget"] is None
    assert data["within_budget"] is None
    assert data["itinerary"][0]["estimated_cost"] is None
