import json
import re
from typing import Any

from backend.app.ai.llm_client import generate_response
from backend.app.rag.retriever import HeritageRetriever
from backend.app.schemas.itinerary import ItineraryRequest


def _extract_json(text: str) -> dict[str, Any]:
    """Extract a JSON object from the model response."""
    cleaned = text.strip()

    # Handle responses wrapped in Markdown code fences.
    cleaned = re.sub(
        r"^```(?:json)?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError as error:
        raise ValueError("The AI returned invalid JSON.") from error

    if not isinstance(result, dict):
        raise ValueError("The AI response must be a JSON object.")

    return result


def generate_itinerary(
    request: ItineraryRequest,
    heritage_context: str | None = None,
) -> dict[str, Any]:
    """Generate an itinerary using retrieved heritage context."""

    # Retrieve heritage information unless context was supplied by the caller.
    if heritage_context is None:
        try:
            retriever = HeritageRetriever()
            query = (
                f"Heritage sites, historical places, architecture, and "
                f"cultural attractions in {request.destination}. "
                f"Traveler interests: "
                f"{', '.join(request.interests) or 'general heritage'}."
            )
            retrieved_chunks = retriever.search(query, top_k=5)

        except (OSError, ValueError, RuntimeError) as error:
            raise RuntimeError(
                "The heritage retrieval service is unavailable."
            ) from error

        context_parts = []

        for chunk in retrieved_chunks:
            title = chunk.get("title", "Untitled source")
            source_url = chunk.get("source_url", "")
            text = chunk.get("text", "")

            context_parts.append(
                f"Title: {title}\n"
                f"Source URL: {source_url}\n"
                f"Content: {text}"
            )

        heritage_context = "\n\n".join(context_parts)

    if not heritage_context.strip():
        heritage_context = (
            "No relevant heritage information was retrieved. "
            "Do not claim that specific places or prices are verified."
        )

    prompt = f"""
You are a heritage travel-planning assistant.

Create a practical itinerary using the traveler's requirements and the
heritage information provided below.

Traveler requirements:
- Destination: {request.destination}
- Trip duration: {request.days} day(s)
- Total budget: INR {request.budget}
- Travelers: {request.travelers}
- Interests: {", ".join(request.interests) or "General heritage"}
- Travel style: {request.travel_style}
- Include food costs: {request.include_food}
- Include transport costs: {request.include_transport}

Available heritage context:
{heritage_context}

Rules:
1. Return ONLY one valid JSON object.
2. Prefer heritage places supported by the supplied context.
3. Do not invent source URLs, entry fees, transport prices, or opening hours.
4. If a cost is unknown, use 0 and explain the uncertainty in assumptions.
5. Use source URLs only when supplied context supports them.
6. Return exactly {request.days} daily plans.
7. Each day's activities must be a JSON array.
8. Use numeric, non-negative values for all estimated costs.
9. If the context is insufficient, state that limitation in assumptions.

Required JSON structure:
{{
  "itinerary": [
    {{
      "title": "Day title",
      "activities": [
        {{
          "place_name": "Heritage place name",
          "description": "Short activity description",
          "estimated_entry_cost": 0,
          "estimated_transport_cost": 0,
          "estimated_food_cost": 0,
          "source_url": null
        }}
      ]
    }}
  ],
  "assumptions": ["List unknown prices or planning assumptions here"]
}}
"""

    try:
        raw_response = generate_response(prompt)
    except (ConnectionError, TimeoutError, OSError, RuntimeError) as error:
        raise RuntimeError(
            "The itinerary AI service is unavailable."
        ) from error

    result = _extract_json(raw_response)

    itinerary = result.get("itinerary")
    assumptions = result.get("assumptions", [])

    if not isinstance(itinerary, list):
        raise ValueError(
            "The AI response must contain an itinerary list."
        )

    if len(itinerary) != request.days:
        raise ValueError(
            f"The AI must return exactly {request.days} daily plans."
        )

    if not isinstance(assumptions, list) or not all(
        isinstance(item, str) for item in assumptions
    ):
        raise ValueError(
            "The assumptions field must be a list of strings."
        )

    return {
        "itinerary": itinerary,
        "assumptions": assumptions,
    }