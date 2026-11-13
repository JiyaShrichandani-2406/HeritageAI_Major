from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_routes_api_returns_matching_city_route_with_ids_and_labels():
    response = client.post(
        "/api/v1/routes",
        json={
            "origin_id": "city-agra",
            "destination_id": "city-fatehpur-sikri",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["origin_id"] == "city-agra"
    assert data["destination_id"] == "city-fatehpur-sikri"
    assert data["origin"] == "Agra"
    assert data["destination"] == "Fatehpur Sikri"
    assert [option["id"] for option in data["options"]] == [
        "agra-fatehpur-sikri-upsrtc-bus"
    ]
    assert data["options"][0]["cost_status"] == "unknown"
    assert data["options"][0]["estimated_cost"] is None
    assert data["options"][0]["estimated_duration_minutes"] is None
    assert data["options"][0]["duration_status"] == "unknown"
    assert "unavailable" in data["message"]


def test_routes_api_returns_place_options_for_exact_direction():
    response = client.post(
        "/api/v1/routes",
        json={
            "origin_id": "place-taj-mahal",
            "destination_id": "place-agra-fort",
        },
    )

    assert response.status_code == 200
    options = response.json()["options"]
    assert {
        option["transport_type"] for option in response.json()["options"]
    } == {"auto-rickshaw", "taxi"}
    assert all(
        option["duration_status"] == "estimated"
        and option["estimated_duration_minutes"] is not None
        for option in options
    )
    assert all(option["cost_status"] == "estimated" for option in options)


def test_routes_api_returns_empty_for_unsupported_or_reversed_routes():
    for origin_id, destination_id in [
        ("city-delhi", "city-agra"),
        ("city-bhopal", "city-agra"),
        ("place-agra-fort", "place-taj-mahal"),
    ]:
        response = client.post(
            "/api/v1/routes",
            json={
                "origin_id": origin_id,
                "destination_id": destination_id,
            },
        )

        assert response.status_code == 200
        assert response.json()["options"] == []
        assert "No transport records" in response.json()["message"]


def test_routes_api_rejects_unknown_location_ids():
    response = client.post(
        "/api/v1/routes",
        json={
            "origin_id": "city-not-in-catalog",
            "destination_id": "city-agra",
        },
    )

    assert response.status_code == 404
