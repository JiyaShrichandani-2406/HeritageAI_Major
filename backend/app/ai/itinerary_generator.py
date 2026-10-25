
import json
import re
from dataclasses import asdict
from typing import Any

from backend.app.ai.llm_client import OllamaTimeoutError, generate_response
from backend.app.rag.retriever import HeritageRetriever
from backend.app.repositories.place_repository import PlaceRepository
from backend.app.repositories.monument_repository import (
    get_monuments,
)
from backend.app.repositories.transport_repository import TransportRepository
from backend.app.repositories.visitor_service_repository import (
    VisitorServiceRepository,
)
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

class UnsupportedDestinationError(ValueError):
    """Raised when no supported heritage place exists for a destination."""


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

def _normalize_assumptions(value: Any) -> list[str]:
    """Coerce the model's assumptions field into a list of non-empty strings."""
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        return []

    cleaned: list[str] = []
    for item in value:
        if isinstance(item, str):
            text = item.strip()
        elif isinstance(item, dict):
            # Use the first string value, e.g. {"assumption": "..."}
            text = next(
                (v.strip() for v in item.values() if isinstance(v, str) and v.strip()),
                "",
            )
        elif item is None:
            text = ""
        else:
            text = str(item).strip()
        if text:
            cleaned.append(text)
    return cleaned

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

    places = PlaceRepository().all()

    # For example, convert "Agra, India" to "agra".
    normalized_destination = (
        destination.split(",")[0].casefold().strip()
    )
    normalized_place_name = _normalize_name(place_name)

    if not normalized_destination:
        return None

    for monument in get_monuments():
        if not _same_place_name(normalized_place_name, monument["name"]):
            continue
        if normalized_destination in monument["city"].casefold():
            return monument["name"]

    for place in places:
        if not _same_place_name(normalized_place_name, place.name):
            continue

        address = place.address.casefold()

        if normalized_destination in address:
            return place.name

    return None


def _normalize_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", name.casefold()).strip()


def _same_place_name(candidate: str, canonical_name: str) -> bool:
    """Match a canonical name and its parenthetical aliases."""
    aliases = [canonical_name.split("(", maxsplit=1)[0].strip()]
    aliases.extend(re.findall(r"\(([^)]+)\)", canonical_name))
    aliases.append(canonical_name)
    return candidate in {_normalize_name(alias) for alias in aliases}


def _supports_destination(destination: str) -> bool:
    """Return whether the local heritage catalog covers this destination."""
    destination_key = destination.split(",")[0].casefold().strip()
    if not destination_key:
        return False

    if any(
        destination_key in monument["city"].casefold()
        for monument in get_monuments()
    ):
        return True

    return any(
        destination_key in place.address.casefold()
        for place in PlaceRepository().all()
    )


def _normalize_activity(activity: Any) -> dict[str, Any]:
    """Validate activity costs and normalize their verification statuses."""
    if not isinstance(activity, dict):
        raise ValueError(
            "Each itinerary activity must be a JSON object."
        )

    normalized = dict(activity)

    for cost_field in COST_FIELDS:
        status_field = COST_STATUS_FIELDS[cost_field]
        value = normalized.get(cost_field)
        status = normalized.get(status_field, "unknown")

        if (
            value is not None
            and (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or value < 0
            )
        ):
            raise ValueError(
                f"{cost_field} must be null or a non-negative number."
            )

        if status not in {"verified", "estimated", "unknown"}:
            raise ValueError(
                f"{status_field} must be verified, estimated, or unknown."
            )

        # Transport costs require a matching sourced option, not a model guess.
        if cost_field == "estimated_transport_cost":
            status = "unknown"
            value = None
        elif value is None or (value == 0 and status != "verified"):
            status = "unknown"

        # The model cannot independently verify a price.
        if status == "verified":
            status = "estimated" if value > 0 else "unknown"

        normalized[status_field] = status

        if status == "unknown":
            normalized[cost_field] = None
        else:
            normalized[cost_field] = value

    return normalized


def _load_travel_references(
    request: ItineraryRequest,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Load route options and services matching the itinerary destination."""
    destination = request.destination.split(",")[0].strip()
    transport_options = (
        TransportRepository()
        .search(
            request.origin.split(",")[0].strip(),
            destination,
        )
        if request.origin
        else []
    )

    destination_key = destination.casefold()
    visitor_services = [
        service
        for service in VisitorServiceRepository().all()
        if destination_key
        in {
            location_part.strip().casefold()
            for location_part in service.location.split(",")
        }
    ]

    return (
        [asdict(option) for option in transport_options],
        [asdict(service) for service in visitor_services],
    )


def generate_itinerary(
    request: ItineraryRequest,
    heritage_context: str | None = None,
) -> dict[str, Any]:
    """Generate an itinerary using retrieved heritage context."""

    if heritage_context is None and not _supports_destination(
        request.destination
    ):
        raise UnsupportedDestinationError(
            f"No heritage or nearby-place data is available for "
            f"{request.destination}. Supported destinations include Agra "
            "and Fatehpur Sikri."
        )

    try:
        transport_options, visitor_services = _load_travel_references(request)
    except (OSError, ValueError, RuntimeError) as error:
        raise RuntimeError(
            "Transport or visitor-service data is unavailable. Check the "
            "processed datasets on the API host."
        ) from error

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

    travel_references = json.dumps(
        {
            "transport_options": transport_options,
            "visitor_services": visitor_services,
        },
        ensure_ascii=False,
        indent=2,
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

Available destination travel references:
{travel_references}

Rules:
1. Return ONLY one valid JSON object.
2. Prefer heritage places supported by the supplied context.
3. Do not invent source URLs, prices, or opening hours.
4. A price generated by you is never verified just because it looks plausible.
5. Do not estimate local or intercity transport costs. Set transport cost to
null and its status to "unknown"; matching sourced route options are listed
separately and are not part of the daily itinerary totals.
6. Use "verified" only if the supplied context explicitly supports that
specific entry or food price and its applicability to these travelers.
7. Use "estimated" for a plausible entry or food planning estimate not
confirmed by a reliable source.
8. Use "unknown" when a reliable amount is unavailable.
9. For an unknown cost, use null and set its status to "unknown". Never imply
that the service is free.
10. Use only URLs present in the supplied context. A heritage page alone
    does not verify ticket or food prices.
11. Return exactly {request.days} daily plans.
12. Include two to four distinct suitable activities per day when the
    supplied heritage information supports them; do not repeat activities
    merely to fill the plan.
13. Each day's activities must be a JSON array.
14. Cost values must be null or numeric and non-negative.
15. Include assumptions explaining unknown costs and estimates.
16. For excluded food or transport costs, use null with status "unknown".
17. Do not claim that budget compliance is verified when relevant costs
    are unknown or merely estimated.
18. Keep each description to eight words or fewer and assumptions concise.
19. Stay within the traveler budget where possible; do not remove all
    recommended activities to force budget compliance.
20. Treat transport and visitor-service references as supplemental options.
    Do not add their costs to activity costs; the response lists them
    separately, and their cost basis may not match this trip.

Required JSON structure:
{{
"itinerary": [
    {{
    "title": "Day title",
    "activities": [
        {{
        "place_name": "Heritage place name",
        "description": "Short activity description",
        "estimated_entry_cost": null,
        "entry_cost_status": "unknown",
        "estimated_transport_cost": null,
        "transport_cost_status": "unknown",
        "estimated_food_cost": null,
        "food_cost_status": "unknown",
        "source_url": null
        }}
    ]
    }}
],
"assumptions": []
}}
"""

    try:
        raw_response = generate_response(
            prompt,
            num_predict=min(2048, max(384, request.days * 384)),
        )
    except (OllamaTimeoutError, TimeoutError) as error:
        raise OllamaTimeoutError(
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

    assumptions = _normalize_assumptions(assumptions)

    if request.origin and not transport_options:
        assumptions.append(
            f"No transport route data is available for "
            f"{request.origin} to {request.destination}; "
            "intercity transport is not included."
        )

    if not visitor_services:
        assumptions.append(
            f"No visitor-service records are available for "
            f"{request.destination}."
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

        if not activities:
            raise RuntimeError(
                f"No supported activities could be generated for day "
                f"{len(normalized_itinerary) + 1}."
            )

        activities = activities[:4]

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

        if not normalized_activities:
            raise RuntimeError(
                f"No supported activities could be generated for day "
                f"{len(normalized_itinerary) + 1}. Confirm the available "
                "heritage and places data covers the requested destination."
            )

        normalized_itinerary.append(
            {
                **daily_plan,
                "activities": normalized_activities,
            }
        )

    return {
        "itinerary": normalized_itinerary,
        "assumptions": list(dict.fromkeys(assumptions)),
        "transport_options": transport_options,
        "visitor_services": visitor_services,
    }