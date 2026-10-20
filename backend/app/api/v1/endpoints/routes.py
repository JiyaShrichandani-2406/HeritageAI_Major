
"""Transport API endpoints (Member 4)."""

from fastapi import APIRouter

from backend.app.schemas.route import RouteRequest, RouteResponse
from backend.app.services.transport_service import find_transport_options

router = APIRouter(tags=["Transport"])


@router.post("/routes", response_model=RouteResponse)
def get_transport_options(request: RouteRequest) -> RouteResponse:
    """Find available transport options between two locations."""
    return find_transport_options(
        origin=request.origin,
        destination=request.destination,
    )
