"""Business logic for visitor services (Member 4)."""

from backend.app.repositories.visitor_service_repository import (
    VisitorServiceRepository,
)
from backend.app.schemas.service import (
    VisitorServiceResponse,
    VisitorServicesResponse,
)


def find_visitor_services(
    category: str | None = None,
    repository: VisitorServiceRepository | None = None,
) -> VisitorServicesResponse:
    """Return visitor services, optionally filtered by category."""

    repo = repository or VisitorServiceRepository()

    if category:
        services = repo.by_category(category)
    else:
        services = repo.all()

    if not services:
        message = (
            "No visitor-service records are available yet. "
            "Service details and costs have not been verified."
        )
    else:
        message = (
            "Visitor services retrieved from the available dataset. "
            "Check each service's cost status and source before relying on it."
        )

    return VisitorServicesResponse(
        category=category,
        services=[
            VisitorServiceResponse(
                id=service.id,
                name=service.name,
                category=service.category,
                location=service.location,
                latitude=service.latitude,
                longitude=service.longitude,
                description=service.description,
                estimated_cost=service.estimated_cost,
                currency=service.currency,
                cost_status=service.cost_status,
                source_url=service.source_url,
            )
            for service in services
        ],
        message=message,
    )
