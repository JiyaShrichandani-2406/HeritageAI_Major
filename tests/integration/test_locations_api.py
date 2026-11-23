from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_locations_endpoint_returns_merged_cities_and_places():
    response = client.get("/api/v1/locations")

    assert response.status_code == 200
    data = response.json()
    cities = {city["id"]: city for city in data["cities"]}
    places = {place["name"]: place for place in data["places"]}

    assert len(cities) == 5
    assert len(places) == 24
    assert places["Taj Mahal"]["city_id"] == "city-agra"
    assert places["Fatehpur Sikri"]["city_id"] == "city-fatehpur-sikri"
    assert places["Keoladeo National Park"]["city_id"] == "city-bharatpur"
    assert places["Chini ka Rauza"]["coordinate_source"] == "nearby_places.json"
