import json
import logging
import math
import re
from dataclasses import asdict
from typing import Any

from backend.app.ai.llm_client import CloudflareTimeoutError, generate_response
from backend.app.rag.retriever import get_retriever
from backend.app.repositories.location_repository import (
    LocationRepository,
)
from backend.app.repositories.transport_repository import TransportRepository
from backend.app.repositories.visitor_service_repository import (
    VisitorServiceRepository,
)
from backend.app.schemas.itinerary import ItineraryRequest
from backend.app.services.transport_service import select_transport_option


logger = logging.getLogger(__name__)

# Keep prompts within the context limits of the configured AI model.
LLM_CONTEXT_TOKENS = 8192


def _compact_json(value: Any) -> str:
    """Serialize without indentation to keep the prompt small."""
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


COST_FIELDS = (
    "estimated_entry_cost",
    "estimated_transport_cost",
    "estimated_food_cost",
    "estimated_guide_cost",
    "estimated_parking_cost",
)

COST_STATUS_FIELDS = {
    "estimated_entry_cost": "entry_cost_status",
    "estimated_transport_cost": "transport_cost_status",
    "estimated_food_cost": "food_cost_status",
    "estimated_guide_cost": "guide_cost_status",
    "estimated_parking_cost": "parking_cost_status",
}


_SERVICE_PLACE_ALIASES = {
    "akbar tomb": "Akbar's Tomb (Sikandra)",
    "mariam tomb": "Tomb of Mariam-uz-Zamani",
}


class UnsupportedDestinationError(ValueError):
    """Raised when no supported heritage place exists for a destination."""


def _validate_source_url(
    source_url: str | None,
    heritage_context: str,
    known_sources: set[str] | None = None,
) -> str | None:
    """Accept source URLs grounded in retrieved or catalogued data."""
    if not isinstance(source_url, str) or not source_url.strip():
        return None

    candidate = source_url.strip()

    if candidate not in heritage_context and candidate not in (known_sources or set()):
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
        # Keep the raw model output so the real cause (truncation, chatter,
        # malformed JSON) can be seen in the server log.
        logger.error(
            "Itinerary LLM returned invalid JSON (%s). Output length=%d. "
            "Start=%r ... End=%r",
            error,
            len(text),
            text[:500],
            text[-300:],
        )
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

    repository = LocationRepository()
    place = repository.find_place(place_name)
    city = repository.find_city(destination) or repository.find_city(
        destination.split(",", maxsplit=1)[0]
    )
    if (
        place
        and place.get("category") != "transit_stop"
        and city
        and place["city_id"] == city["id"]
    ):
        return place["name"]
    return None


def _supports_destination(destination: str) -> bool:
    """Return whether the local heritage catalog covers this destination."""
    repository = LocationRepository()
    city = repository.find_city(destination) or repository.find_city(
        destination.split(",", maxsplit=1)[0]
    )
    return bool(
        city
        and any(place["city_id"] == city["id"] for place in repository.places())
    )


def _resolve_place_area(place_name: str) -> str:
    """Return the catalog city for a selected place-to-place endpoint."""
    place = LocationRepository().find_place(place_name)
    if place:
        return place["city"]

    raise UnsupportedDestinationError(
        f"No place data is available for {place_name}."
    )


def _resolve_route_location_id(
    location_id: str | None,
    location_name: str | None,
    itinerary_mode: str | None,
) -> str | None:
    """Resolve a request endpoint to its canonical city or place ID."""
    locations = LocationRepository()
    selected_location = (
        locations.get_location(location_id) if location_id else None
    )
    if location_id and selected_location is None:
        raise UnsupportedDestinationError(
            f"No location data is available for ID {location_id}."
        )

    if itinerary_mode == "city_to_city":
        matched_location = (
            locations.find_city(location_name.split(",", maxsplit=1)[0])
            if location_name
            else selected_location
        )
        if location_name and matched_location is None:
            raise UnsupportedDestinationError(
                "City-to-city routes require a catalogued origin city."
            )
        if selected_location and selected_location["id"] not in {
            city["id"] for city in locations.cities()
        }:
            raise UnsupportedDestinationError(
                "City-to-city routes require city location IDs."
            )
    elif itinerary_mode == "place_to_place":
        matched_location = (
            locations.find_place(location_name) if location_name else selected_location
        )
        if location_name and matched_location is None:
            raise UnsupportedDestinationError(
                "Place-to-place routes require catalogued heritage places."
            )
        if selected_location and (
            selected_location["id"] not in {
                place["id"] for place in locations.places()
            }
            or selected_location.get("category") == "transit_stop"
        ):
            raise UnsupportedDestinationError(
                "Place-to-place routes require selectable heritage places."
            )
    else:
        matched_location = None
        if location_name:
            matched_location = locations.find_city(
                location_name.split(",", maxsplit=1)[0]
            ) or locations.find_place(location_name)

    if location_id:
        if location_name and (
            matched_location is None or matched_location["id"] != location_id
        ):
            raise UnsupportedDestinationError(
                "The location ID does not match the selected location."
            )
        return location_id
    return matched_location["id"] if matched_location else None


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
    service_destination: str | None = None,
    transport_repository: TransportRepository | None = None,
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    """Load route options and services matching the itinerary destination."""
    destination = request.destination.split(",")[0].strip()
    origin_id = _resolve_route_location_id(
        request.origin_id,
        request.origin,
        request.itinerary_mode,
    )
    destination_id = _resolve_route_location_id(
        request.destination_id,
        request.destination,
        request.itinerary_mode,
    )
    repository = transport_repository or TransportRepository()
    all_transport_options = [
        asdict(option) for option in repository.all()
    ]
    transport_options = [
        option
        for option in all_transport_options
        if option["origin_id"] == origin_id
        and option["destination_id"] == destination_id
    ]

    destination_key = (
        service_destination or destination
    ).split(",")[0].casefold().strip()
    service_areas = {destination_key}
    if request.itinerary_mode == "place_to_place":
        locations = LocationRepository()
        origin_place = (
            next(
                (
                    place
                    for place in locations.places()
                    if place["id"] == request.origin_id
                ),
                None,
            )
            if request.origin_id
            else locations.find_place(request.origin or "")
        )
        if origin_place:
            service_areas.add(origin_place["city"].casefold().strip())
    visitor_services = [
        service
        for service in VisitorServiceRepository().all()
        if service_areas.intersection(
            {
                location_part.strip().casefold()
                for location_part in service.location.split(",")
            }
        )
    ]

    return (
        transport_options,
        [asdict(service) for service in visitor_services],
        all_transport_options,
    )


def _distance_km(first: dict[str, Any], second: dict[str, Any]) -> float | None:
    """Return straight-line distance when both catalog coordinates exist."""
    coordinates = (
        first.get("latitude"),
        first.get("longitude"),
        second.get("latitude"),
        second.get("longitude"),
    )
    if any(value is None for value in coordinates):
        return None

    lat1, lon1, lat2, lon2 = map(math.radians, coordinates)
    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1
    haversine = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    )
    return 6371 * 2 * math.asin(math.sqrt(haversine))


def _has_sourced_visit_timing(heritage_context: str) -> bool:
    """Detect explicit visit-time information paired with a cited source."""
    for source_context in re.split(r"\n\s*\n", heritage_context):
        if not re.search(r"https?://\S+", source_context):
            continue
        has_opening_hours = bool(
            re.search(
                r"\b(?:opening[\s_-]*hours?|open(?:s|ing)?|closed)\b",
                source_context,
                flags=re.IGNORECASE,
            )
            and re.search(
                r"\b(?:\d{1,2}(?::\d{2})?\s*(?:a\.?m\.?|p\.?m\.?)|"
                r"(?:[01]?\d|2[0-3]):[0-5]\d)\b",
                source_context,
                flags=re.IGNORECASE,
            )
        )
        has_visit_duration = bool(
            re.search(
                r"\b(?:visit duration|allow|spend|takes)\b",
                source_context,
                flags=re.IGNORECASE,
            )
            and re.search(
                r"\b\d+(?:\.\d+)?\s*(?:hours?|hrs?|minutes?|mins?)\b",
                source_context,
                flags=re.IGNORECASE,
            )
        )
        if has_opening_hours or has_visit_duration:
            return True
    return False


def _order_day_activities(
    activities: list[dict[str, Any]],
    places_by_id: dict[str, dict[str, Any]],
    routes_by_pair: dict[tuple[str, str], list[dict[str, Any]]],
    *,
    start_location_id: str | None = None,
    final_location_id: str | None = None,
) -> list[dict[str, Any]]:
    """Order stops by nearest catalog coordinates, preserving required endpoints."""
    remaining = list(activities)
    if start_location_id is None and remaining:
        start_location_id = remaining[0]["_location_id"]
    final_activity = None
    if final_location_id:
        final_activity = next(
            (
                activity
                for activity in remaining
                if activity["_location_id"] == final_location_id
            ),
            None,
        )
        if final_activity:
            remaining.remove(final_activity)

    ordered: list[dict[str, Any]] = []
    current = places_by_id.get(start_location_id or "")
    while remaining:
        if current is None:
            ordered.extend(remaining)
            break

        def rank(activity: dict[str, Any]) -> tuple[float, int, str]:
            place_id = activity["_location_id"]
            place = places_by_id[place_id]
            distance = _distance_km(current, place)
            has_sourced_route = bool(
                routes_by_pair.get((current["id"], place_id))
            )
            return (
                distance if distance is not None else float("inf"),
                0 if has_sourced_route else 1,
                place_id,
            )

        next_activity = min(remaining, key=rank)
        remaining.remove(next_activity)
        ordered.append(next_activity)
        current = places_by_id[next_activity["_location_id"]]

    if final_activity:
        ordered.append(final_activity)
    return ordered


def _make_endpoint_activity(
    place: dict[str, Any],
    description: str,
) -> dict[str, Any]:
    return {
        "_location_id": place["id"],
        "place_name": place["name"],
        "description": description,
        "estimated_entry_cost": None,
        "entry_cost_status": "unknown",
        "estimated_transport_cost": None,
        "transport_cost_status": "unknown",
        "estimated_travel_duration_minutes": None,
        "travel_duration_status": "unknown",
        "transport_type": None,
        "transport_source_url": None,
        "transport_notes": None,
        "estimated_food_cost": None,
        "food_cost_status": "unknown",
        "source_url": place.get("source_url"),
    }


def _finalize_activity_order(
    itinerary: list[dict[str, Any]],
    places: list[dict[str, Any]],
    transport_options: list[dict[str, Any]],
    request: ItineraryRequest,
    starting_place: dict[str, Any] | None,
    ending_place: dict[str, Any] | None,
    visitor_services: list[dict[str, Any]],
    heritage_context: str,
    respect_generated_order: bool,
) -> list[dict[str, Any]]:
    places_by_id = {place["id"]: place for place in places}
    known_sources = {
        source
        for place in places
        for source in place.get("source_urls", [])
    }
    known_sources.update(
        place["source_url"]
        for place in places
        if place.get("source_url")
    )

    locations = LocationRepository()
    services_by_place: dict[str, list[dict[str, Any]]] = {}
    for service in visitor_services:
        service_location = service.get("location", "").split(",", maxsplit=1)[0]
        place = locations.find_place(service_location)
        if not place:
            alias = _SERVICE_PLACE_ALIASES.get(
                service_location.casefold().strip()
            )
            if alias:
                place = locations.find_place(alias)
        if place:
            services_by_place.setdefault(place["id"], []).append(service)

    seen: set[str] = set()
    for day in itinerary:
        unique_activities = []
        for activity in day["activities"]:
            place_id = activity["_location_id"]
            if place_id in seen:
                continue
            seen.add(place_id)
            unique_activities.append(activity)
        day["activities"] = unique_activities

    if starting_place:
        start_id = starting_place["id"]
        for day in itinerary:
            day["activities"] = [
                activity
                for activity in day["activities"]
                if activity["_location_id"] != start_id
            ]
        itinerary[0]["activities"].insert(
            0, _make_endpoint_activity(starting_place, "Start at selected place.")
        )

    if ending_place:
        end_id = ending_place["id"]
        for day in itinerary:
            day["activities"] = [
                activity
                for activity in day["activities"]
                if activity["_location_id"] != end_id
            ]
        itinerary[-1]["activities"].append(
            _make_endpoint_activity(
                ending_place,
                "Arrive at selected destination.",
            )
        )

    if starting_place and ending_place and starting_place["id"] == ending_place["id"]:
        raise UnsupportedDestinationError(
            "The starting and destination places must be different."
        )

    for day in itinerary:
        activities = day["activities"]
        if not activities:
            raise RuntimeError(
                "Removing duplicate stops left a day without any distinct "
                "supported activities."
            )
        while len(activities) > 4:
            removable_index = next(
                (
                    index
                    for index, activity in enumerate(activities)
                    if activity["_location_id"]
                    not in {
                        place["id"]
                        for place in (starting_place, ending_place)
                        if place
                    }
                ),
                None,
            )
            if removable_index is None:
                raise RuntimeError(
                    "Selected itinerary endpoints exceed the daily activity limit."
                )
            activities.pop(removable_index)

    routes_by_pair: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for option in transport_options:
        routes_by_pair.setdefault(
            (option["origin_id"], option["destination_id"]), []
        ).append(option)

    previous_day_location_id = None
    for day_index, day in enumerate(itinerary):
        start_location_id = previous_day_location_id
        if day_index == 0:
            if starting_place:
                start_location_id = starting_place["id"]
            elif request.itinerary_mode == "city_to_city":
                start_city = (
                    locations.find_city(request.origin or "")
                    or {}
                )
                start_location_id = start_city.get("id")
        final_location_id = (
            ending_place["id"]
            if day_index == len(itinerary) - 1 and ending_place
            else None
        )
        if respect_generated_order:
            ordered_activities = list(day["activities"])
            if final_location_id:
                final_activity = next(
                    (
                        activity
                        for activity in ordered_activities
                        if activity["_location_id"] == final_location_id
                    ),
                    None,
                )
                if final_activity:
                    ordered_activities.remove(final_activity)
                    ordered_activities.append(final_activity)
            day["activities"] = ordered_activities
        else:
            day["activities"] = _order_day_activities(
                day["activities"],
                places_by_id,
                routes_by_pair,
                start_location_id=start_location_id,
                final_location_id=final_location_id,
            )

        previous_id = start_location_id
        for activity in day["activities"]:
            place_id = activity["_location_id"]
            activity["estimated_transport_cost"] = None
            activity["transport_cost_status"] = "unknown"
            activity["estimated_travel_duration_minutes"] = None
            activity["travel_duration_status"] = "unknown"
            activity["transport_type"] = None
            activity["transport_source_url"] = None
            activity["transport_notes"] = None
            activity["estimated_guide_cost"] = None
            activity["guide_cost_status"] = "unknown"
            activity["guide_source_url"] = None
            activity["estimated_parking_cost"] = None
            activity["parking_cost_status"] = "unknown"
            activity["parking_source_url"] = None

            if (
                day_index == 0
                and previous_id
                and request.itinerary_mode == "city_to_city"
            ):
                destination_city_id = places_by_id[place_id]["city_id"]
                route = select_transport_option(
                    routes_by_pair.get(
                        (previous_id, destination_city_id), []
                    ),
                    request.travel_style,
                )
                if route:
                    if request.include_transport:
                        activity["estimated_transport_cost"] = route[
                            "estimated_cost"
                        ]
                        activity["transport_cost_status"] = route[
                            "cost_status"
                        ]
                    activity["estimated_travel_duration_minutes"] = route[
                        "estimated_duration_minutes"
                    ]
                    activity["travel_duration_status"] = route[
                        "duration_status"
                    ]
                    activity["transport_type"] = route["transport_type"]
                    activity["transport_source_url"] = route["source_url"]
                    activity["transport_notes"] = route["notes"]
            elif previous_id and previous_id != place_id:
                route = select_transport_option(
                    routes_by_pair.get((previous_id, place_id), []),
                    request.travel_style,
                )
                if route:
                    if request.include_transport:
                        activity["estimated_transport_cost"] = route[
                            "estimated_cost"
                        ]
                        activity["transport_cost_status"] = route[
                            "cost_status"
                        ]
                    activity["estimated_travel_duration_minutes"] = (
                        route["estimated_duration_minutes"]
                    )
                    activity["travel_duration_status"] = route[
                        "duration_status"
                    ]
                    activity["transport_type"] = route["transport_type"]
                    activity["transport_source_url"] = route["source_url"]
                    activity["transport_notes"] = route["notes"]

            place_services = services_by_place.get(place_id, [])
            if request.include_guides:
                guide_options = [
                    service
                    for service in place_services
                    if service["category"] == "guide"
                ]
                guide = next(
                    (
                        service
                        for service in guide_options
                        if "licensed" in service["id"].casefold()
                    ),
                    guide_options[0] if guide_options else None,
                )
                if guide:
                    activity["estimated_guide_cost"] = guide[
                        "estimated_cost"
                    ]
                    activity["guide_cost_status"] = guide["cost_status"]
                    activity["guide_source_url"] = guide["source_url"]

            if request.include_parking and request.parking_vehicle_type:
                parking_ids = {
                    "two_wheeler": "two-wheeler",
                    "car_taxi": "car-taxi",
                    "tempo_traveller": "tempo-traveller",
                    "bus": "-bus",
                }
                parking = next(
                    (
                        service
                        for service in place_services
                        if service["category"] == "parking"
                        and parking_ids[request.parking_vehicle_type]
                        in service["id"].casefold()
                    ),
                    None,
                )
                if parking:
                    activity["estimated_parking_cost"] = parking[
                        "estimated_cost"
                    ]
                    activity["parking_cost_status"] = parking["cost_status"]
                    activity["parking_source_url"] = parking["source_url"]

            activity["source_url"] = _validate_source_url(
                activity.get("source_url"),
                heritage_context,
                known_sources,
            )
            previous_id = place_id
        if day["activities"]:
            previous_day_location_id = day["activities"][-1]["_location_id"]

    for day in itinerary:
        for activity in day["activities"]:
            activity.pop("_location_id", None)
    return itinerary


def _generate_itinerary(
    request: ItineraryRequest,
    heritage_context: str | None = None,
    *,
    activity_destination: str | None = None,
    journey_instructions: str = "",
    starting_place: dict[str, Any] | None = None,
    ending_place: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate and validate an itinerary for a selected planning area."""
    activity_destination = activity_destination or request.destination

    if heritage_context is None and not _supports_destination(
        activity_destination
    ):
        raise UnsupportedDestinationError(
            f"No heritage or nearby-place data is available for "
            f"{activity_destination}. Supported destinations include Agra "
            "and Fatehpur Sikri."
        )

    try:
        transport_repository = TransportRepository()
        (
            transport_options,
            visitor_services,
            all_transport_options,
        ) = _load_travel_references(
            request,
            service_destination=activity_destination,
            transport_repository=transport_repository,
        )
    except UnsupportedDestinationError:
        raise
    except (OSError, ValueError, RuntimeError) as error:
        raise RuntimeError(
            "Transport or visitor-service data is unavailable. Check the "
            "processed datasets on the API host."
        ) from error

    if heritage_context is None:
        try:
            retriever = get_retriever()

            query = (
                f"Heritage sites, historical places, architecture, and "
                f"cultural attractions in {activity_destination}. "
                f"Traveler interests: "
                f"{', '.join(request.interests) or 'general heritage'}."
            )

            retrieved_chunks = retriever.search(query, top_k=3)

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

    locations = LocationRepository()
    destination_city = locations.find_city(activity_destination)
    if not destination_city:
        raise UnsupportedDestinationError(
            f"No location catalog entry exists for {activity_destination}."
        )
    candidate_places = [
        place
        for place in locations.places()
        if place["city_id"] == destination_city["id"]
        and place.get("category") != "transit_stop"
    ]
    if starting_place and all(
        place["id"] != starting_place["id"] for place in candidate_places
    ):
        candidate_places.append(starting_place)
    if ending_place and all(
        place["id"] != ending_place["id"] for place in candidate_places
    ):
        candidate_places.append(ending_place)
    candidate_place_ids = {place["id"] for place in candidate_places}
    local_transport_options = [
        {
            "origin_id": option["origin_id"],
            "destination_id": option["destination_id"],
            "transport_type": option["transport_type"],
            "estimated_cost": option["estimated_cost"],
            "currency": option["currency"],
            "estimated_duration_minutes": option[
                "estimated_duration_minutes"
            ],
            "duration_status": option["duration_status"],
            "cost_status": option["cost_status"],
            "source_url": option["source_url"],
        }
        for option in all_transport_options
        if option["origin_id"] in candidate_place_ids
        and option["destination_id"] in candidate_place_ids
    ]
    # Only what the model needs to pick places; ordering, sources and costs
    # are re-applied from the catalog in code afterwards.
    attraction_catalog = [
        {
            "id": place["id"],
            "name": place["name"],
            "category": place["category"],
        }
        for place in candidate_places
    ]
    prompt_services = [
        {
            key: service.get(key)
            for key in (
                "id",
                "category",
                "location",
                "estimated_cost",
                "cost_status",
            )
        }
        for service in visitor_services
    ]

    travel_references = _compact_json(
        {
            "transport_options": transport_options,
            "local_transport_routes": local_transport_options,
            "visitor_services": prompt_services,
        }
    )

    prompt = f"""
You are a careful heritage travel-planning assistant.

Create a practical itinerary using the traveler's requirements and the
heritage information provided below.

Traveler requirements:
- Starting location: {request.origin or "Not specified"}
- Destination: {request.destination}
- Planning area: {activity_destination}
- Journey instructions: {journey_instructions or "Plan the destination itinerary."}
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

Available catalogued attractions and nearby places:
{_compact_json(attraction_catalog)}

Rules:
1. Return ONLY one valid JSON object.
2. Select attractions only from the supplied catalog and heritage context.
   Nearby places may be included when their categories suit the traveler.
   Do not add a location absent from the catalog.
3. Do not invent source URLs, prices, or opening hours.
4. A price generated by you is never verified just because it looks plausible.
5. Only use route costs and durations from the exact-direction local route
   records above. Never infer a route from coordinates or a reverse route.
   Leave unsupported travel cost unknown.
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
20. Opening hours and visit durations are not structured in the attraction
    catalog. Use them only when reliable information is explicitly present
    in the heritage context; prioritize those constraints and otherwise do
    not invent time windows.
21. Arrange each day's attractions to reduce straight-line travel between
    catalog coordinates. This is a geographic ordering aid, not road routing.
22. Do not repeat an attraction within or across days.
23. Put the selected starting place first and destination place last for
    place-to-place itineraries.
24. Transport costs and durations supported by exact local route records are
    associated with the activity reached by that leg. Do not count the
    separate intercity route options in day costs.

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
        # Each activity is ~100 tokens of JSON (up to 4 per day) plus
        # assumptions, so the old 384-tokens-per-day cap truncated the JSON.
        raw_response = generate_response(
            prompt,
            num_predict=min(4096, max(1024, request.days * 900)),
            json_mode=True,
            num_ctx=LLM_CONTEXT_TOKENS,
        )
    except (CloudflareTimeoutError, TimeoutError) as error:
        raise CloudflareTimeoutError(
            "Cloudflare Workers AI timed out generating the itinerary. "
            "Please try again later."
        ) from error
    except (ConnectionError, OSError, RuntimeError) as error:
        raise RuntimeError(
            "Cloudflare Workers AI is unavailable. Verify "
            "CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_API_TOKEN, and "
            "CLOUDFLARE_TEXT_MODEL on the API host."
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
    location_repository = LocationRepository()
    endpoint_ids = {
        place["id"]
        for place in (starting_place, ending_place)
        if place
    }

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

        if len(activities) > 4:
            raise ValueError(
                f"Each itinerary day may contain at most four activities; "
                f"day {len(normalized_itinerary) + 1} contains "
                f"{len(activities)}."
            )

        normalized_activities = []

        for activity in activities:
            normalized = _normalize_activity(activity)

            # Validate the generated place against the canonical dataset.
            canonical_name = _validate_place(
                normalized.get("place_name", ""),
                activity_destination,
            )
            place = location_repository.find_place(
                normalized.get("place_name", "")
            )
            if (
                canonical_name is None
                and place
                and place["id"] in endpoint_ids
                and place.get("category") != "transit_stop"
            ):
                canonical_name = place["name"]

            if canonical_name is None:
                assumptions.append(
                    f"Unsupported place removed: "
                    f"{normalized.get('place_name', 'Unknown place')}."
                )
                continue

            normalized["place_name"] = canonical_name
            normalized["_location_id"] = place["id"]

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

    normalized_itinerary = _finalize_activity_order(
        normalized_itinerary,
        location_repository.places(),
        all_transport_options,
        request,
        starting_place,
        ending_place,
        visitor_services,
        heritage_context,
        _has_sourced_visit_timing(heritage_context),
    )
    if not _has_sourced_visit_timing(heritage_context):
        assumptions.append(
            "Opening hours and visit durations were not available as "
            "structured location data; stop order is based on coordinates, "
            "not time windows."
        )
    else:
        assumptions.append(
            "Explicit cited visit timing in the heritage context was "
            "prioritized over geographic ordering."
        )

    return {
        "itinerary": normalized_itinerary,
        "assumptions": list(dict.fromkeys(assumptions)),
        "transport_options": transport_options,
        "local_transport_options": local_transport_options,
        "visitor_services": visitor_services,
    }


def generate_city_to_city_itinerary(
    request: ItineraryRequest,
    heritage_context: str | None = None,
) -> dict[str, Any]:
    """Generate a city itinerary whose destination is fixed to Agra."""
    if request.destination.casefold() != "agra":
        raise ValueError(
            "City-to-city itineraries must use Agra as the destination."
        )

    return _generate_itinerary(
        request,
        heritage_context,
        activity_destination="Agra",
        journey_instructions=(
            f"Travel from the selected origin city ({request.origin or 'unspecified'}) "
            "to Agra, then plan heritage activities in Agra."
        ),
    )


def generate_place_to_place_itinerary(
    request: ItineraryRequest,
    heritage_context: str | None = None,
) -> dict[str, Any]:
    """Generate an itinerary between two catalogued heritage places."""
    if not request.origin:
        raise ValueError(
            "Place-to-place itineraries require a starting place."
        )

    start_area = _resolve_place_area(request.origin)
    destination_area = _resolve_place_area(request.destination)
    start_name = _validate_place(request.origin, start_area)
    destination_name = _validate_place(
        request.destination,
        destination_area,
    )
    if start_name is None or destination_name is None:
        raise UnsupportedDestinationError(
            "Both place-to-place endpoints must match supported heritage places."
        )
    locations = LocationRepository()
    start_place = locations.find_place(start_name)
    destination_place = locations.find_place(destination_name)
    if not start_place or not destination_place:
        raise UnsupportedDestinationError(
            "Both place-to-place endpoints must exist in the location catalog."
        )

    return _generate_itinerary(
        request,
        heritage_context,
        activity_destination=destination_area,
        journey_instructions=(
            f"Plan a journey starting at {start_name} and ending at "
            f"{destination_name}. Include the starting place as the first "
            "activity and the destination as the final activity."
        ),
        starting_place=start_place,
        ending_place=destination_place,
    )


def generate_itinerary(
    request: ItineraryRequest,
    heritage_context: str | None = None,
) -> dict[str, Any]:
    """Dispatch itinerary generation to the selected mode."""
    if request.itinerary_mode == "city_to_city":
        return generate_city_to_city_itinerary(request, heritage_context)
    if request.itinerary_mode == "place_to_place":
        return generate_place_to_place_itinerary(request, heritage_context)
    return _generate_itinerary(request, heritage_context)