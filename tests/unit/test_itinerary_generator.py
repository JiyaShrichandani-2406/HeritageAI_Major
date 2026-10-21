
import pytest

from backend.app.ai.itinerary_generator import (
    _extract_json,
    _load_travel_references,
    generate_itinerary,
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
        cost_status="estimated",
        source_url="https://example.com/train",
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
        def search(self, origin, destination):
            assert (origin, destination) == ("Delhi", "Agra")
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

    transport_options, visitor_services = _load_travel_references(
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
    _, visitor_services = _load_travel_references(
        ItineraryRequest(
            destination="Agra",
            budget=5000,
            days=1,
        )
    )

    assert [service["id"] for service in visitor_services] == [
        "agra-fort-licensed-guides",
        "agra-fort-audio-guides",
    ]
    assert all(
        service["cost_status"] == "unknown"
        and service["estimated_cost"] is None
        and service["source_url"]
        == "https://agra.nic.in/tourist-place/agra-fort/"
        for service in visitor_services
    )


def test_multiple_activities_are_allowed_and_transport_is_not_guessed(
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
    assert all(
        activity["estimated_transport_cost"] is None
        and activity["transport_cost_status"] == "unknown"
        for activity in activities
    )
    assert "Do not estimate local or intercity transport costs" in captured["prompt"]
    assert "two to four distinct suitable activities per day" in captured["prompt"]
    assert captured["num_predict"] == 512


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
