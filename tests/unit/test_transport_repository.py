import json

import pytest

from backend.app.repositories.location_repository import LocationRepository
from backend.app.repositories.transport_repository import (
    TransportDataError,
    TransportRepository,
)


def test_transport_records_use_resolvable_location_ids():
    locations = LocationRepository()
    options = TransportRepository().all()
    location_ids = {
        location["id"]
        for location in [*locations.cities(), *locations.places()]
    }

    assert len(options) == 51
    assert all(
        option.origin_id in location_ids
        and option.destination_id in location_ids
        for option in options
    )
    assert all(
        (option.estimated_cost is None) == (option.cost_status == "unknown")
        for option in options
    )
    assert all(
        (option.estimated_duration_minutes is None)
        == (option.duration_status == "unknown")
        for option in options
    )


def test_transport_search_matches_only_the_exact_direction():
    repository = TransportRepository()

    forward = repository.search("place-taj-mahal", "place-agra-fort")
    reverse = repository.search("place-agra-fort", "place-taj-mahal")

    assert {option.transport_type for option in forward} == {
        "auto-rickshaw",
        "taxi",
        "metro",
    }
    assert reverse == []


def test_unsupported_city_routes_are_not_invented():
    repository = TransportRepository()

    assert repository.search("city-bhopal", "city-delhi") == []
    assert repository.search("city-bhopal", "city-agra") == []


def test_search_supports_sourced_city_and_place_route_records():
    repository = TransportRepository()

    city_route = repository.search(
        "city-agra",
        "city-fatehpur-sikri",
    )
    place_route = repository.search(
        "place-fatehpur-sikri-parking-area",
        "place-fatehpur-sikri-monument-gate",
    )

    assert sorted(route.id for route in city_route) == [
        "agra-fatehpur-sikri-train",
        "agra-fatehpur-sikri-upsrtc-bus",
    ]
    assert [route.id for route in place_route] == [
        "fatehpur-sikri-parking-battery-bus"
    ]
    bus_route = next(
        route
        for route in city_route
        if route.id == "agra-fatehpur-sikri-upsrtc-bus"
    )
    assert bus_route.cost_status == "unknown"
    assert bus_route.duration_status == "unknown"
    assert bus_route.estimated_cost is None
    assert bus_route.estimated_duration_minutes is None


@pytest.mark.parametrize(
    ("origin_id", "destination_id", "message"),
    [
        ("city-unknown", "city-agra", "Unknown origin location ID"),
        ("city-agra", "place-unknown", "Unknown destination location ID"),
    ],
)
def test_search_rejects_unknown_location_ids(
    origin_id,
    destination_id,
    message,
):
    with pytest.raises(ValueError, match=message):
        TransportRepository().search(origin_id, destination_id)


def _route_record(**overrides):
    return {
        "id": "test-agra-fatehpur-route",
        "origin_id": "city-agra",
        "destination_id": "city-fatehpur-sikri",
        "transport_type": "bus",
        "estimated_cost": 50,
        "currency": "INR",
        "estimated_duration_minutes": 100,
        "duration_status": "estimated",
        "cost_status": "estimated",
        "source_url": None,
        "notes": "",
        **overrides,
    }


def test_unknown_cost_and_duration_are_returned_without_zero_fallback(tmp_path):
    data_path = tmp_path / "transport.json"
    data_path.write_text(
        json.dumps(
            [
                _route_record(
                    estimated_cost=None,
                    estimated_duration_minutes=None,
                    duration_status="unknown",
                    cost_status="unknown",
                )
            ]
        ),
        encoding="utf-8",
    )

    route = TransportRepository(data_path).search(
        "city-agra",
        "city-fatehpur-sikri",
    )[0]

    assert route.estimated_cost is None
    assert route.cost_status == "unknown"
    assert route.estimated_duration_minutes is None
    assert route.duration_status == "unknown"


@pytest.mark.parametrize(
    "record",
    [
        _route_record(origin_id="city-not-real"),
        _route_record(estimated_cost=-1),
        _route_record(estimated_duration_minutes=1.5),
        _route_record(
            estimated_cost=None,
            cost_status="estimated",
        ),
        _route_record(
            estimated_duration_minutes=None,
            duration_status="estimated",
        ),
        _route_record(cost_status="unsupported"),
    ],
)
def test_malformed_or_inconsistent_route_data_fails_explicitly(
    tmp_path,
    record,
):
    data_path = tmp_path / "transport.json"
    data_path.write_text(json.dumps([record]), encoding="utf-8")

    with pytest.raises(TransportDataError, match="malformed"):
        TransportRepository(data_path).all()


def test_missing_transport_dataset_has_a_clear_error(tmp_path):
    with pytest.raises(TransportDataError, match="not found"):
        TransportRepository(tmp_path / "missing.json").all()
