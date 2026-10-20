
"""Transport API endpoints (Member 4)."""

from fastapi import APIRouter, HTTPException, status

from backend.app.repositories.transport_repository import TransportDataError
from backend.app.schemas.common import ErrorResponse, ValidationErrorResponse
from backend.app.schemas.route import RouteRequest, RouteResponse
from backend.app.services.transport_service import find_transport_options

router = APIRouter(tags=["Transport"])


@router.post(
    "/routes",
    response_model=RouteResponse,
    responses={
        422: {
            "description": "The route request failed validation.",
            "model": ValidationErrorResponse,
        },
        503: {
            "description": "The transport dataset is unavailable.",
            "model": ErrorResponse,
        },
        500: {
            "description": "An unexpected route lookup error occurred.",
            "model": ErrorResponse,
        },
    },
)
def get_transport_options(request: RouteRequest) -> RouteResponse:
    """Find available transport options between two locations."""
    try:
        return find_transport_options(
            origin=request.origin,
            destination=request.destination,
        )
    except TransportDataError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The transport dataset is unavailable.",
        ) from error
