"""Business logic for transport options (Member 4)."""

from typing import Any

from backend.app.repositories.transport_repository import TransportRepository
from backend.app.repositories.location_repository import LocationRepository
from backend.app.schemas.route import RouteResponse, TransportOptionResponse


def select_transport_option(
    options: list[dict[str, Any]],
    travel_style: str,
) -> dict[str, Any] | None:
    """Choose one sourced route using the requested cost/time preference."""
    if not options:
        return None

    if travel_style == "budget":
        return min(
            options,
            key=lambda option: (
                option["estimated_cost"] is None,
                option["estimated_cost"] or 0,
                option["estimated_duration_minutes"] is None,
                option["estimated_duration_minutes"] or 0,
            ),
        )
    return min(
        options,
        key=lambda option: (
            option["estimated_duration_minutes"] is None,
            option["estimated_duration_minutes"] or 0,
            option["estimated_cost"] is None,
            option["estimated_cost"] or 0,
        ),
    )


def find_transport_options(
    origin_id: str,
    destination_id: str,
    repository: TransportRepository | None = None,
) -> RouteResponse:
    """Find sourced transport options between canonical location IDs."""

    locations = LocationRepository()
    origin_location = locations.get_location(origin_id)
    destination_location = locations.get_location(destination_id)
    if not origin_location or not destination_location:
        raise LookupError("The route contains an unknown location ID.")

    repo = repository or TransportRepository()
    options = repo.search(origin_id, destination_id)

    if not options:
        message = (
            "No transport records are available for this route yet. "
            "No fare or journey duration is available."
        )
    elif all(
        option.cost_status == "unknown"
        and option.estimated_cost is None
        and option.duration_status == "unknown"
        and option.estimated_duration_minutes is None
        for option in options
    ):
        message = (
            "Route records exist, but fares and journey durations are "
            "unavailable or unverified."
        )
    else:
        message = (
            "Transport options are based on available route records. "
            "Check the cost and duration statuses and sources before travelling."
        )

    return RouteResponse(
        origin_id=origin_id,
        destination_id=destination_id,
        origin=origin_location["name"],
        destination=destination_location["name"],
        options=[
            TransportOptionResponse(
                id=option.id,
                origin_id=option.origin_id,
                destination_id=option.destination_id,
                origin=option.origin,
                destination=option.destination,
                transport_type=option.transport_type,
                estimated_cost=option.estimated_cost,
                currency=option.currency,
                estimated_duration_minutes=option.estimated_duration_minutes,
                duration_status=option.duration_status,
                cost_status=option.cost_status,
                source_url=option.source_url,
                notes=option.notes,
            )
            for option in options
        ],
        message=message,
    )
