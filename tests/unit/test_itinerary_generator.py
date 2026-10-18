
import pytest

from backend.app.ai.itinerary_generator import (
    _extract_json,
    generate_itinerary,
    _validate_source_url,
)
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
