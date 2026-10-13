
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
    assert data["within_budget"] is True
    assert data["remaining_budget"] == 2200
    assert data["assumptions"] == ["Costs are sample estimates."]


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


def test_create_itinerary_missing_destination():
    response = client.post(
        "/api/v1/itinerary",
        json={
            "budget": 3000,
            "days": 2,
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
    assert response.json()["detail"] == (
        "The itinerary generation service is unavailable."
    )
