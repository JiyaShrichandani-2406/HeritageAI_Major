import pytest

from backend.app.ai.itinerary_generator import (
    _extract_json,
    _load_travel_references,
    _resolve_place_area,
    _supports_destination,
    _validate_place,
    UnsupportedDestinationError,
    generate_itinerary,
    generate_place_to_place_itinerary,
    _validate_source_url,
)
from backend.app.models.transport import TransportOption
from backend.app.models.visitor_service import VisitorService
from backend.app.schemas.itinerary import ItineraryRequest


@pytest.mark.parametrize(
    "response",
    [
        '{"itinerary": [], "assumptions": []}',
        '```json\n{"itinerary": [], "assumptions": []}\n```\nExplanation',
        'Here is the result: {"itinerary": [], "assumptions": []} Done.',
    ],
)
def test_extract_json_ignores_model_formatting_and_trailing_text(response):
    assert _extract_json(response) == {
        "itinerary": [],
        "assumptions": [],
    }


def test_extract_json_rejects_malformed_json():
    with pytest.raises(ValueError, match="The AI returned invalid JSON"):
        _extract_json('```json\n{"itinerary": }\n```')


def test_itinerary_generation_rejects_malformed_model_json(monkeypatch):
    monkeypatch.setattr(
        "backend.app.ai.itinerary_generator.generate_response",
        lambda *args, **kwargs: '{"itinerary": ',
    )

    with pytest.raises(ValueError, match="The AI returned invalid JSON"):
        generate_itinerary(
            ItineraryRequest(destination="Agra", budget=10000, days=1),
            heritage_context="Heritage context",
        )


def test_generated_source_url_must_be_grounded_in_context():
    context = (
        "Title: Agra Fort\n"
        "Source URL: https://agra.nic.in/tourist-place/agra-fort/\n"
        "Content: Agra Fort is in Agra."
    )

    assert _validate_source_url(
        "https://agra.nic.in/tourist-place/agra-fort/",
        context,
    ) == "https://agra.nic.in/tourist-place/agra-fort/"

    assert _validate_source_url(
        "https://redfort.in",
        context,
    ) is None


def test_ram_bagh_parenthetical_alias_is_supported():
    assert _validate_place("Ram Bagh", "Agra") == "Ram Bagh (Aram Bagh)"


def test_destination_support_reflects_local_heritage_data():
    assert _supports_destination("Agra") is True
    assert _supports_destination("Fatehpur Sikri") is True
    assert _supports_destination("Bhopal") is False


def test_place_to_place_endpoints_resolve_to_supported_areas():
    assert _resolve_place_area("Taj Mahal") == "Agra"
    assert _resolve_place_area("Fatehpur Sikri") == "Fatehpur Sikri"


def test_itinerary_request_trims_location_ids_and_canonicalizes_agra():
    request = ItineraryRequest(
        itinerary_mode="city_to_city",
        origin="Delhi",
        origin_id=" city-delhi ",
        destination="agra",
        destination_id=" city-agra ",
        budget=10000,
        days=1,
    )

    assert request.origin_id == "city-delhi"
    assert request.destination_id == "city-agra"
    assert request.destination == "Agra"


def test_place_to_place_generation_uses_destination_area(monkeypatch):
    captured = {}

    def fake_generate(request, heritage_context, **kwargs):
        captured.update(kwargs)
        return {"itinerary": [], "assumptions": []}

    monkeypatch.setattr(
        "backend.app.ai.itinerary_generator._generate_itinerary",
        fake_generate,
    )

    request = ItineraryRequest(
        itinerary_mode="place_to_place",
        origin="Taj Mahal",
        destination="Agra Fort",
        budget=10000,
        days=1,
    )
    generate_place_to_place_itinerary(request, heritage_context="Context")

    assert captured["activity_destination"] == "Agra"
    assert "Taj Mahal" in captured["journey_instructions"]
    assert "Agra Fort" in captured["journey_instructions"]


def test_place_to_place_generation_validates_against_destination_area(
    monkeypatch,
):
    monkeypatch.setattr(
        "backend.app.ai.itinerary_generator.generate_response",
        lambda *args, **kwargs: (
            '{"itinerary":[{"title":"Day 1","activities":[{'
            '"place_name":"Agra Fort",'
            '"description":"Explore the fort",'
            '"estimated_entry_cost":null,'
            '"estimated_transport_cost":null,'
            '"estimated_food_cost":null'
            '}]}],"assumptions":[]}'
        ),
    )

    result = generate_itinerary(
        ItineraryRequest(
            itinerary_mode="place_to_place",
            origin="Taj Mahal",
            destination="Agra Fort",
            budget=10000,
            days=1,
        ),
        heritage_context="Verified heritage context.",
    )

    assert [
        activity["place_name"]
        for activity in result["itinerary"][0]["activities"]
    ] == ["Taj Mahal", "Agra Fort"]


def test_unsupported_destination_has_a_clear_error():
    with pytest.raises(UnsupportedDestinationError, match="Bhopal"):
        generate_itinerary(
            ItineraryRequest(destination="Bhopal", budget=10000, days=1)
        )


def test_generated_ungrounded_source_url_is_removed(monkeypatch):
    monkeypatch.setattr(
        "backend.app.ai.itinerary_generator.generate_response",
        lambda *args, **kwargs: (
            '{"itinerary":[{"title":"Day 1","activities":[{'
            '"place_name":"Taj Mahal",'
            '"description":"Visit the monument",'
            '"estimated_entry_cost":null,'
            '"estimated_transport_cost":null,'
            '"estimated_food_cost":null,'
            '"source_url":"https://untrusted.example/source"'
            '}]}],"assumptions":[]}'
        ),
    )
    monkeypatch.setattr(
        "backend.app.ai.itinerary_generator._validate_place",
        lambda place_name, destination: place_name,
    )

    result = generate_itinerary(
        ItineraryRequest(destination="Agra", budget=10000, days=1),
        heritage_context="Verified heritage context.",
    )

    assert result["itinerary"][0]["activities"][0]["source_url"] is None


def test_itinerary_generation_reports_ollama_timeout(monkeypatch):
    def timeout(*args, **kwargs):
        raise TimeoutError("request timed out")

    monkeypatch.setattr(
        "backend.app.ai.itinerary_generator.generate_response",
        timeout,
    )

    request = ItineraryRequest(
        destination="Bhopal",
        budget=10000,
        days=1,
    )

    with pytest.raises(RuntimeError, match="Ollama timed out generating"):
        generate_itinerary(request, heritage_context="Heritage context")


def test_itinerary_generation_rejects_days_without_supported_activities(
    monkeypatch,
):
    monkeypatch.setattr(
        "backend.app.ai.itinerary_generator.generate_response",
        lambda *args, **kwargs: (
            '{"itinerary":[{"title":"Day 1","activities":[{'
            '"place_name":"Taj Mahal",'
            '"description":"Visit the monument",'
            '"estimated_entry_cost":0,'
            '"estimated_transport_cost":0,'
            '"estimated_food_cost":0'
            '}]}],"assumptions":[]}'
        ),
    )
    monkeypatch.setattr(
        "backend.app.ai.itinerary_generator._validate_place",
        lambda place_name, destination: None,
    )

    request = ItineraryRequest(
        destination="Bhopal",
        budget=10000,
        days=1,
    )

    with pytest.raises(
        RuntimeError,
        match="No supported activities could be generated for day 1",
    ):
        generate_itinerary(request, heritage_context="Heritage context")


def test_itinerary_generation_rejects_empty_day(monkeypatch):
    monkeypatch.setattr(
        "backend.app.ai.itinerary_generator.generate_response",
        lambda *args, **kwargs: (
            '{"itinerary":[{"title":"Day 1","activities":[]}],'
            '"assumptions":[]}'
        ),
    )

    request = ItineraryRequest(
        destination="Bhopal",
        budget=10000,
        days=1,
    )

    with pytest.raises(
        RuntimeError,
        match="No supported activities could be generated for day 1",
    ):
        generate_itinerary(request, heritage_context="Heritage context")


def test_itinerary_generation_rejects_empty_second_day(monkeypatch):
    monkeypatch.setattr(
        "backend.app.ai.itinerary_generator.generate_response",
        lambda *args, **kwargs: (
            '{"itinerary":['
            '{"title":"Day 1","activities":[{"place_name":"Taj Mahal",'
            '"description":"Visit the monument",'
            '"estimated_entry_cost":null}]},'
            '{"title":"Day 2","activities":[]}'
            '],"assumptions":[]}'
        ),
    )
    monkeypatch.setattr(
        "backend.app.ai.itinerary_generator._validate_place",
        lambda place_name, destination: place_name,
    )

    with pytest.raises(
        RuntimeError,
        match="No supported activities could be generated for day 2",
    ):
        generate_itinerary(
            ItineraryRequest(destination="Agra", budget=10000, days=2),
            heritage_context="Heritage context",
        )


def test_itinerary_loads_route_and_destination_service_references(monkeypatch):
    route = TransportOption(
        id="delhi-agra-train",
        origin="Delhi",
        destination="Agra",
        transport_type="train",
        estimated_cost=500,
        currency="INR",
        estimated_duration_minutes=120,
        duration_status="estimated",
        cost_status="estimated",
        source_url="https://example.com/train",
        origin_id="city-delhi",
        destination_id="city-agra",
    )
    agra_service = VisitorService(
        id="agra-guide",
        name="Agra guide",
        category="guide",
        location="Agra, Uttar Pradesh",
        latitude=None,
        longitude=None,
        description="Local heritage guide",
        estimated_cost=1000,
        currency="INR",
        cost_status="estimated",
        source_url="https://example.com/guide",
    )
    delhi_service = VisitorService(
        id="delhi-guide",
        name="Delhi guide",
        category="guide",
        location="Delhi",
        latitude=None,
        longitude=None,
        description="Local heritage guide",
        estimated_cost=1000,
        currency="INR",
        cost_status="estimated",
        source_url="https://example.com/delhi-guide",
    )

    class StubTransportRepository:
        def all(self):
            return [route]

    class StubVisitorServiceRepository:
        def all(self):
            return [agra_service, delhi_service]

    monkeypatch.setattr(
        "backend.app.ai.itinerary_generator.TransportRepository",
        StubTransportRepository,
    )
    monkeypatch.setattr(
        "backend.app.ai.itinerary_generator.VisitorServiceRepository",
        StubVisitorServiceRepository,
    )

    transport_options, visitor_services, _ = _load_travel_references(
        ItineraryRequest(
            origin="Delhi",
            destination="Agra, India",
            budget=10000,
            days=1,
        )
    )

    assert [option["id"] for option in transport_options] == [
        "delhi-agra-train"
    ]
    assert [service["id"] for service in visitor_services] == [
        "agra-guide"
    ]


def test_agras_sourced_visitor_services_are_included_without_inventing_costs():
    _, visitor_services, _ = _load_travel_references(
        ItineraryRequest(
            destination="Agra",
            budget=5000,
            days=1,
        )
    )

    services_by_id = {
        service["id"]: service for service in visitor_services
    }
    assert {
        "agra-fort-licensed-guides",
        "agra-fort-audio-guides",
        "taj-mahal-licensed-guides",
        "taj-mahal-parking-car-taxi",
    }.issubset(services_by_id)
    assert services_by_id["agra-fort-licensed-guides"][
        "estimated_cost"
    ] == 400
    assert services_by_id["agra-fort-licensed-guides"][
        "cost_status"
    ] == "estimated"


def test_fatehpur_sikri_transport_and_services_are_sourced():
    transport_options, visitor_services, _ = _load_travel_references(
        ItineraryRequest(
            origin="Agra",
            destination="Fatehpur Sikri",
            budget=5000,
            days=1,
        )
    )

    assert [option["id"] for option in transport_options] == [
        "agra-fatehpur-sikri-upsrtc-bus"
    ]
    assert transport_options[0]["cost_status"] == "unknown"
    assert transport_options[0]["estimated_cost"] is None
    assert [service["id"] for service in visitor_services] == [
        "fatehpur-sikri-licensed-guides"
    ]
    assert visitor_services[0]["estimated_cost"] == 625
    assert visitor_services[0]["cost_status"] == "estimated"


@pytest.mark.parametrize(
    ("origin", "origin_id"),
    [
        ("Bhopal", "city-bhopal"),
        ("Delhi", "city-delhi"),
    ],
)
def test_city_to_agra_route_options_reflect_only_sourced_records(
    origin,
    origin_id,
):
    transport_options, _, _ = _load_travel_references(
        ItineraryRequest(
            itinerary_mode="city_to_city",
            origin=origin,
            origin_id=origin_id,
            destination="Agra",
            destination_id="city-agra",
            budget=5000,
            days=1,
        )
    )

    # Neither route is present in the transport dataset; do not infer one.
    assert transport_options == []


def test_itinerary_route_ids_must_match_selected_locations():
    with pytest.raises(
        UnsupportedDestinationError,
        match="does not match the selected location",
    ):
        _load_travel_references(
            ItineraryRequest(
                itinerary_mode="city_to_city",
                origin="Delhi",
                origin_id="city-bhopal",
                destination="Agra",
                destination_id="city-agra",
                budget=5000,
                days=1,
            )
        )


def test_sourced_local_transport_cost_and_duration_are_attached_to_the_leg(
    monkeypatch,
):
    raw_response = (
        '{"itinerary":[{"title":"Day 1","activities":['
        '{"place_name":"Taj Mahal","description":"Explore the monument",'
        '"estimated_entry_cost":50,"entry_cost_status":"estimated",'
        '"estimated_transport_cost":250,'
        '"transport_cost_status":"estimated",'
        '"estimated_food_cost":null,"food_cost_status":"unknown"},'
        '{"place_name":"Agra Fort","description":"Visit the fort",'
        '"estimated_entry_cost":100,"entry_cost_status":"estimated",'
        '"estimated_transport_cost":400,'
        '"transport_cost_status":"estimated",'
        '"estimated_food_cost":null,"food_cost_status":"unknown"}'
        ']}],"assumptions":[]}'
    )
    captured = {}

    def fake_generate_response(prompt, **kwargs):
        captured["prompt"] = prompt
        captured["num_predict"] = kwargs["num_predict"]
        captured["json_mode"] = kwargs.get("json_mode")
        return raw_response

    monkeypatch.setattr(
        "backend.app.ai.itinerary_generator.generate_response",
        fake_generate_response,
    )
    monkeypatch.setattr(
        "backend.app.ai.itinerary_generator._validate_place",
        lambda place_name, destination: place_name,
    )

    result = generate_itinerary(
        ItineraryRequest(destination="Agra", budget=10000, days=1),
        heritage_context="Verified heritage context.",
    )

    activities = result["itinerary"][0]["activities"]
    assert len(activities) == 2
    assert activities[0]["estimated_transport_cost"] is None
    assert activities[1]["estimated_transport_cost"] == 65
    assert activities[1]["transport_cost_status"] == "estimated"
    assert activities[1]["estimated_travel_duration_minutes"] == 10
    assert activities[1]["transport_type"] == "auto-rickshaw"
    assert activities[1]["transport_source_url"]
    assert "exact-direction local route" in captured["prompt"]
    assert "Agra Fort" in captured["prompt"]
    assert "two to four distinct suitable activities per day" in captured["prompt"]
    assert captured["num_predict"] == 1024
    assert captured["json_mode"] is True


def test_place_to_place_keeps_selected_endpoints_and_removes_duplicate_stops(
    monkeypatch,
):
    monkeypatch.setattr(
        "backend.app.ai.itinerary_generator.generate_response",
        lambda *args, **kwargs: (
            '{"itinerary":[{"title":"Day 1","activities":['
            '{"place_name":"Taj Mahal","description":"Start the heritage walk"},'
            '{"place_name":"Taj Mahal","description":"Duplicate stop"},'
            '{"place_name":"Agra Fort","description":"Explore the fort"}'
            ']}],"assumptions":[]}'
        ),
    )

    result = generate_itinerary(
        ItineraryRequest(
            itinerary_mode="place_to_place",
            origin="Taj Mahal",
            destination="Agra Fort",
            budget=10000,
            days=1,
        ),
        heritage_context="Verified heritage context.",
    )

    activities = result["itinerary"][0]["activities"]
    assert [activity["place_name"] for activity in activities] == [
        "Taj Mahal",
        "Agra Fort",
    ]
    assert activities[-1]["estimated_transport_cost"] == 65
    assert activities[-1]["estimated_travel_duration_minutes"] == 10


@pytest.mark.parametrize(
    ("origin", "destination", "expected_cost"),
    [
        ("Taj Mahal", "Chini ka Rauza", 85),
        ("Taj Mahal", "Akbar's Tomb (Sikandra)", 195),
    ],
)
def test_other_place_to_place_pairs_keep_endpoints_and_exact_route(
    monkeypatch,
    origin,
    destination,
    expected_cost,
):
    monkeypatch.setattr(
        "backend.app.ai.itinerary_generator.generate_response",
        lambda *args, **kwargs: (
            '{"itinerary":[{"title":"Day 1","activities":['
            f'{{"place_name":"{origin}","description":"Start the trip"}},'
            f'{{"place_name":"{destination}","description":"Visit destination"}}'
            ']}],"assumptions":[]}'
        ),
    )

    result = generate_itinerary(
        ItineraryRequest(
            itinerary_mode="place_to_place",
            origin=origin,
            destination=destination,
            budget=10000,
            days=1,
        ),
        heritage_context="Verified heritage context.",
    )

    activities = result["itinerary"][0]["activities"]
    assert activities[0]["place_name"] == origin
    assert activities[-1]["place_name"] == destination
    assert activities[-1]["estimated_transport_cost"] == expected_cost
    assert activities[-1]["transport_cost_status"] == "estimated"
    assert activities[-1]["estimated_travel_duration_minutes"] is not None


def test_missing_reverse_route_does_not_create_transport_estimates(
    monkeypatch,
):
    monkeypatch.setattr(
        "backend.app.ai.itinerary_generator.generate_response",
        lambda *args, **kwargs: (
            '{"itinerary":[{"title":"Day 1","activities":['
            '{"place_name":"Agra Fort","description":"Start at the fort"},'
            '{"place_name":"Taj Mahal","description":"Visit the monument"}'
            ']}],"assumptions":[]}'
        ),
    )

    result = generate_itinerary(
        ItineraryRequest(
            itinerary_mode="place_to_place",
            origin="Agra Fort",
            destination="Taj Mahal",
            budget=10000,
            days=1,
        ),
        heritage_context="Verified heritage context.",
    )

    destination_activity = result["itinerary"][0]["activities"][-1]
    assert destination_activity["estimated_transport_cost"] is None
    assert destination_activity["transport_cost_status"] == "unknown"
    assert destination_activity["estimated_travel_duration_minutes"] is None
    assert destination_activity["transport_type"] is None


def test_transport_costs_are_omitted_when_user_excludes_them(monkeypatch):
    monkeypatch.setattr(
        "backend.app.ai.itinerary_generator.generate_response",
        lambda *args, **kwargs: (
            '{"itinerary":[{"title":"Day 1","activities":['
            '{"place_name":"Taj Mahal","description":"Explore the monument"},'
            '{"place_name":"Agra Fort","description":"Visit the fort"}'
            ']}],"assumptions":[]}'
        ),
    )

    result = generate_itinerary(
        ItineraryRequest(
            origin="Delhi",
            destination="Agra",
            budget=10000,
            days=1,
            include_transport=False,
        ),
        heritage_context="Verified heritage context.",
    )

    fort_activity = next(
        activity
        for activity in result["itinerary"][0]["activities"]
        if activity["place_name"] == "Agra Fort"
    )
    assert fort_activity["estimated_transport_cost"] is None
    assert fort_activity["transport_cost_status"] == "unknown"
    assert fort_activity["estimated_travel_duration_minutes"] == 10
    assert fort_activity["transport_type"] == "auto-rickshaw"


def test_selected_guide_and_vehicle_parking_costs_are_sourced(monkeypatch):
    monkeypatch.setattr(
        "backend.app.ai.itinerary_generator.generate_response",
        lambda *args, **kwargs: (
            '{"itinerary":[{"title":"Day 1","activities":['
            '{"place_name":"Taj Mahal","description":"Visit the monument"}'
            ']}],"assumptions":[]}'
        ),
    )

    result = generate_itinerary(
        ItineraryRequest(
            destination="Agra",
            budget=10000,
            days=1,
            include_food=False,
            include_transport=False,
            include_guides=True,
            include_parking=True,
            parking_vehicle_type="car_taxi",
        ),
        heritage_context="Verified heritage context.",
    )

    activity = result["itinerary"][0]["activities"][0]
    assert activity["estimated_guide_cost"] == 1300
    assert activity["guide_cost_status"] == "estimated"
    assert activity["estimated_parking_cost"] == 100
    assert activity["parking_cost_status"] == "estimated"


def test_selected_cost_without_matching_service_stays_unknown(monkeypatch):
    monkeypatch.setattr(
        "backend.app.ai.itinerary_generator.generate_response",
        lambda *args, **kwargs: (
            '{"itinerary":[{"title":"Day 1","activities":['
            '{"place_name":"Agra Fort","description":"Visit the fort"}'
            ']}],"assumptions":[]}'
        ),
    )

    result = generate_itinerary(
        ItineraryRequest(
            destination="Agra",
            budget=10000,
            days=1,
            include_food=False,
            include_transport=False,
            include_guides=True,
            include_parking=True,
            parking_vehicle_type="car_taxi",
        ),
        heritage_context="Verified heritage context.",
    )

    activity = result["itinerary"][0]["activities"][0]
    assert activity["estimated_guide_cost"] == 400
    assert activity["guide_cost_status"] == "estimated"
    assert activity["estimated_parking_cost"] is None
    assert activity["parking_cost_status"] == "unknown"


def test_itinerary_order_uses_nearby_catalog_coordinates():
    from backend.app.ai.itinerary_generator import _order_day_activities
    from backend.app.repositories.location_repository import LocationRepository

    places = LocationRepository().places()
    places_by_id = {place["id"]: place for place in places}
    activities = [
        {"_location_id": "place-chini-ka-rauza", "place_name": "Chini ka Rauza"},
        {"_location_id": "place-taj-mahal", "place_name": "Taj Mahal"},
        {"_location_id": "place-agra-fort", "place_name": "Agra Fort"},
    ]

    ordered = _order_day_activities(
        activities,
        places_by_id,
        {},
        start_location_id="place-taj-mahal",
    )

    assert [activity["place_name"] for activity in ordered] == [
        "Taj Mahal",
        "Agra Fort",
        "Chini ka Rauza",
    ]


def test_sourced_opening_hours_preserve_ai_schedule_order(monkeypatch):
    monkeypatch.setattr(
        "backend.app.ai.itinerary_generator.generate_response",
        lambda *args, **kwargs: (
            '{"itinerary":[{"title":"Day 1","activities":['
            '{"place_name":"Taj Mahal","description":"Visit early"},'
            "{\"place_name\":\"Akbar's Tomb (Sikandra)\","
            "\"description\":\"Visit the tomb\"},"
            '{"place_name":"Agra Fort","description":"Visit the fort"}'
            ']}],"assumptions":[]}'
        ),
    )
    context = (
        "Taj Mahal opening hours are 9:00 AM to 5:00 PM. "
        "Source URL: https://example.org/verified-hours"
    )

    result = generate_itinerary(
        ItineraryRequest(destination="Agra", budget=10000, days=1),
        heritage_context=context,
    )

    assert [
        activity["place_name"]
        for activity in result["itinerary"][0]["activities"]
    ] == ["Taj Mahal", "Akbar's Tomb (Sikandra)", "Agra Fort"]
    assert any("cited visit timing" in item for item in result["assumptions"])


def test_itinerary_generation_rejects_more_than_four_activities(
    monkeypatch,
):
    activities = ",".join(
        (
            '{"place_name":"Taj Mahal","description":"Visit the monument",'
            '"estimated_entry_cost":null,'
            '"estimated_transport_cost":null,'
            '"estimated_food_cost":null}'
        )
        for _ in range(5)
    )
    monkeypatch.setattr(
        "backend.app.ai.itinerary_generator.generate_response",
        lambda *args, **kwargs: (
            '{"itinerary":[{"title":"Day 1","activities":['
            f'{activities}'
            ']}],"assumptions":[]}'
        ),
    )

    with pytest.raises(ValueError, match="at most four activities"):
        generate_itinerary(
            ItineraryRequest(destination="Agra", budget=10000, days=1),
            heritage_context="Verified heritage context.",
        )