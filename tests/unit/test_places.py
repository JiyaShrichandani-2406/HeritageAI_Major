import json
import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.api.v1.endpoints import places as places_endpoint  # noqa: E402
from app.ingestion.import_places import validate_row  # noqa: E402
from app.models.place import CATEGORIES  # noqa: E402
from app.repositories.place_repository import PlaceRepository, PlacesDataError  # noqa: E402
from app.services.places_service import PlacesService, get_places_service, haversine_km  # noqa: E402

TAJ = (27.1751, 78.0421)
DATA = ROOT / "data" / "processed" / "nearby_places.json"


@pytest.fixture()
def service():
    return PlacesService(PlaceRepository(DATA))


@pytest.fixture()
def client(service):
    app = FastAPI()
    app.include_router(places_endpoint.router, prefix="/api/v1/places")
    app.dependency_overrides[get_places_service] = lambda: service
    return TestClient(app)


def test_haversine_zero_and_known_distance():
    assert haversine_km(*TAJ, *TAJ) == 0
    # Taj Mahal -> Agra Fort is roughly 2 km
    assert 1.5 < haversine_km(*TAJ, 27.1795, 78.0211) < 3.0


def test_results_sorted_and_within_radius(service):
    res = service.find_nearby(*TAJ, radius_km=10, limit=50)
    dists = [p.distance_km for p in res]
    assert dists == sorted(dists) and all(d <= 10 for d in dists)
    assert res[0].id == "taj-mahal"


def test_radius_excludes_far_places(service):
    ids = {p.id for p in service.find_nearby(*TAJ, radius_km=10, limit=50)}
    assert "fatehpur-sikri" not in ids
    ids = {p.id for p in service.find_nearby(*TAJ, radius_km=60, limit=50)}
    assert "fatehpur-sikri" in ids


def test_category_filter_and_limit(service):
    res = service.find_nearby(*TAJ, radius_km=100, category="garden", limit=50)
    assert res and all(p.category == "garden" for p in res)
    assert len(service.find_nearby(*TAJ, radius_km=100, limit=2)) == 2


def test_endpoint_ok(client):
    r = client.get("/api/v1/places/nearby", params={"latitude": TAJ[0], "longitude": TAJ[1], "radius_km": 5, "limit": 3})
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == len(body["places"]) <= 3
    assert set(body["places"][0]) == {"id", "name", "category", "latitude", "longitude", "address", "distance_km", "source_url"}


@pytest.mark.parametrize("params", [
    {"latitude": 95, "longitude": 78},
    {"latitude": 27, "longitude": 200},
    {"latitude": 27, "longitude": 78, "radius_km": 0},
    {"latitude": 27, "longitude": 78, "limit": 0},
    {"latitude": 27, "longitude": 78, "category": "spaceport"},
    {"longitude": 78},
])
def test_endpoint_rejects_bad_input(client, params):
    assert client.get("/api/v1/places/nearby", params=params).status_code == 422


def test_endpoint_empty_result_is_valid(client):
    r = client.get("/api/v1/places/nearby", params={"latitude": 0, "longitude": 0})
    assert r.status_code == 200 and r.json() == {"count": 0, "places": []}


def test_missing_data_file_gives_503():
    app = FastAPI()
    app.include_router(places_endpoint.router, prefix="/api/v1/places")
    app.dependency_overrides[get_places_service] = lambda: PlacesService(PlaceRepository(Path("/nope.json")))
    r = TestClient(app).get("/api/v1/places/nearby", params={"latitude": 27, "longitude": 78})
    assert r.status_code == 503
    with pytest.raises(PlacesDataError):
        PlaceRepository(Path("/nope.json")).all()


def test_processed_data_quality():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    ids = [p["id"] for p in data]
    assert len(ids) == len(set(ids)) and data
    for p in data:
        assert p["category"] in CATEGORIES
        assert -90 <= p["latitude"] <= 90 and -180 <= p["longitude"] <= 180
        assert p["source_url"].startswith("http")


def test_import_validation_rejects_bad_rows():
    good = dict(id="a", name="A", category="monument", latitude="27", longitude="78", address="x", source_url="https://x.org")
    assert validate_row(good, 2, set())[1] == []
    assert validate_row({**good, "category": "zzz"}, 2, set())[1]
    assert validate_row({**good, "latitude": "abc"}, 2, set())[1]
    assert validate_row({**good, "source_url": "ftp"}, 2, set())[1]
    assert validate_row(good, 2, {"a"})[1]
