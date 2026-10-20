"""Business logic for transport options (Member 4)."""

from backend.app.repositories.transport_repository import TransportRepository
from backend.app.schemas.route import RouteResponse, TransportOptionResponse


def find_transport_options(
    origin: str,
    destination: str,
    repository: TransportRepository | None = None,
) -> RouteResponse:
    """Find stored transport options between two locations."""

    repo = repository or TransportRepository()
    options = repo.search(origin, destination)

    if not options:
        message = (
            "No transport records are available for this route yet. "
            "Fares and journey durations have not been verified."
        )
    else:
        message = (
            "Transport options retrieved from the available dataset. "
            "Check each option's cost status and source before travelling."
        )

    return RouteResponse(
        origin=origin.strip(),
        destination=destination.strip(),
        options=[
            TransportOptionResponse(
                id=option.id,
                origin=option.origin,
                destination=option.destination,
                transport_type=option.transport_type,
                estimated_cost=option.estimated_cost,
                currency=option.currency,
                estimated_duration_minutes=option.estimated_duration_minutes,
                cost_status=option.cost_status,
                source_url=option.source_url,
                notes=option.notes,
            )
            for option in options
        ],
        message=message,
    )
