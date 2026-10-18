
import json
import re
from typing import Any

from backend.app.ai.llm_client import generate_response
from backend.app.rag.retriever import HeritageRetriever
from backend.app.repositories.place_repository import PlaceRepository
from backend.app.schemas.itinerary import ItineraryRequest


COST_FIELDS = (
    "estimated_entry_cost",
    "estimated_transport_cost",
    "estimated_food_cost",
)

COST_STATUS_FIELDS = {
    "estimated_entry_cost": "entry_cost_status",
    "estimated_transport_cost": "transport_cost_status",
    "estimated_food_cost": "food_cost_status",
}


def _validate_source_url(
    source_url: str | None,
    heritage_context: str,
) -> str | None:
    """Accept a source URL only when it appears in the supplied context."""
    if not isinstance(source_url, str) or not source_url.strip():
        return None

    candidate = source_url.strip()

    if candidate not in heritage_context:
        return None

    return candidate


def _extract_json(text: str) -> dict[str, Any]:
    """Extract a JSON object from the model response."""
    fenced_json = re.search(
        r"```(?:json)?\s*(.*?)\s*```",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    candidate = (
        fenced_json.group(1)
        if fenced_json
        else text.strip()
    )

    object_start = candidate.find("{")

    if object_start >= 0:
        candidate = candidate[object_start:]

    try:
        result, _ = json.JSONDecoder().raw_decode(candidate)
    except json.JSONDecodeError as error:
        raise ValueError("The AI returned invalid JSON.") from error

    if not isinstance(result, dict):
        raise ValueError("The AI response must be a JSON object.")

    return result


def _validate_place(
    place_name: str,
    destination: str,
) -> str | None:
    """Return a canonical place name if it matches the destination."""
    if not isinstance(place_name, str) or not place_name.strip():
        return None

    if not isinstance(destination, str) or not destination.strip():
        return None

    try:
        places = PlaceRepository().all()
    except (OSError, ValueError, RuntimeError):
        return None

    # For example, convert "Agra, India" to "agra".
    normalized_destination = (
        destination.split(",")[0].casefold().strip()
    )
    normalized_place_name = place_name.casefold().strip()

    if not normalized_destination:
        return None

    for place in places:
        if place.name.casefold().strip() != normalized_place_name:
            continue

        address = place.address.casefold()

        if normalized_destination in address:
            return place.name

    return None


def _normalize_activity(activity: Any) -> dict[str, Any]:
    """Validate activity costs and normalize their verification statuses."""
    if not isinstance(activity, dict):
        raise ValueError(
            "Each itinerary activity must be a JSON object."
        )

    normalized = dict(activity)

    for cost_field in COST_FIELDS:
        status_field = COST_STATUS_FIELDS[cost_field]
        value = normalized.get(cost_field, 0)
        status = normalized.get(status_field, "unknown")

        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or value < 0
        ):
            raise ValueError(
                f"{cost_field} must be a non-negative number."
            )

        if status not in {"verified", "estimated", "unknown"}:
            raise ValueError(
                f"{status_field} must be verified, estimated, or unknown."
            )

        # A zero placeholder must not be interpreted as a free service.
        if value == 0 and status != "verified":
            status = "unknown"

        # The model cannot independently verify a price.
        if status == "verified":
            status = "estimated" if value > 0 else "unknown"

        normalized[status_field] = status

        if status == "unknown":
            normalized[cost_field] = 0

    return normalized


def generate_itinerary(
    request: ItineraryRequest,
    heritage_context: str | None = None,
) -> dict[str, Any]:
    """Generate an itinerary using retrieved heritage context."""

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
                "Heritage retrieval is unavailable. Ensure the vector store "
                "and embedding model are available on the API host."
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
            "No prices can be considered verified."
        )

    prompt = f"""
You are a careful heritage travel-planning assistant.

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
3. Do not invent source URLs, prices, or opening hours.
4. A price generated by you is never verified just because it looks plausible.
5. Use "verified" only if the supplied context explicitly supports that
   specific price and its applicability to these travelers.
6. Use "estimated" for a plausible planning estimate not confirmed by a
   reliable source.
7. Use "unknown" when a reliable amount is unavailable.
8. For an unknown cost, use numeric 0 only as a placeholder and set its
   status to "unknown". Never imply that the service is free.
9. Use only URLs present in the supplied context. A heritage page alone
   does not verify ticket, food, or transport prices.
10. Return exactly {request.days} daily plans.
11. Each day's activities must be a JSON array.
12. Cost values must be numeric and non-negative.
13. Include assumptions explaining unknown costs and estimates.
14. For excluded food or transport costs, use 0 with status "unknown".
15. Do not claim that budget compliance is verified when relevant costs
    are unknown or merely estimated.
16. Include no more than one activity per day. Keep each description to
    eight words or fewer and assumptions concise.

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
          "entry_cost_status": "unknown",
          "estimated_transport_cost": 0,
          "transport_cost_status": "unknown",
          "estimated_food_cost": 0,
          "food_cost_status": "unknown",
          "source_url": null
        }}
      ]
    }}
  ],
  "assumptions": ["Explain estimates, unknown prices, and limitations"]
}}
"""

    try:
        raw_response = generate_response(
            prompt,
            num_predict=min(8192, max(192, request.days * 160)),
        )
    except TimeoutError as error:
        raise RuntimeError(
            "Ollama timed out generating the itinerary. Verify Ollama is "
            "reachable from the API host and increase "
            "OLLAMA_TIMEOUT_SECONDS if needed."
        ) from error
    except (ConnectionError, OSError, RuntimeError) as error:
        raise RuntimeError(
            "Ollama is unavailable to the API. Verify OLLAMA_URL and "
            "OLLAMA_MODEL on the API host."
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

    normalized_itinerary = []

    for daily_plan in itinerary:
        if not isinstance(daily_plan, dict):
            raise ValueError(
                "Each daily plan must be a JSON object."
            )

        activities = daily_plan.get("activities", [])

        if not isinstance(activities, list):
            raise ValueError(
                "Each day's activities must be a JSON array."
            )

        normalized_activities = []

        for activity in activities:
            normalized = _normalize_activity(activity)

            # Validate the generated place against the canonical dataset.
            canonical_name = _validate_place(
                normalized.get("place_name", ""),
                request.destination,
            )

            if canonical_name is None:
                assumptions.append(
                    f"Unsupported place removed: "
                    f"{normalized.get('place_name', 'Unknown place')}."
                )
                continue

            normalized["place_name"] = canonical_name

            # Reject source URLs that are not present in the context.
            normalized["source_url"] = _validate_source_url(
                normalized.get("source_url"),
                heritage_context,
            )

            normalized_activities.append(normalized)

        normalized_itinerary.append(
            {
                **daily_plan,
                "activities": normalized_activities,
            }
        )

    # Add an assumption for each unknown cost.
    for day in normalized_itinerary:
        for activity in day["activities"]:
            for cost_field, status_field in COST_STATUS_FIELDS.items():
                if activity[status_field] == "unknown":
                    assumptions.append(
                        f"{activity.get('place_name', 'Activity')}: "
                        f"{cost_field} is UNKNOWN."
                    )

    return {
        "itinerary": normalized_itinerary,
        "assumptions": list(dict.fromkeys(assumptions)),
    }
