
"""Visitor services API endpoints (Member 4)."""

from typing import Literal

from fastapi import APIRouter, HTTPException, Query, status

from backend.app.repositories.visitor_service_repository import (
    VisitorServicesDataError,
)
from backend.app.schemas.common import ErrorResponse, ValidationErrorResponse
from backend.app.schemas.service import VisitorServicesResponse
from backend.app.services.visitor_services import find_visitor_services

router = APIRouter(tags=["Visitor Services"])

ServiceCategory = Literal["food", "market", "guide", "taxi", "other"]


@router.get(
    "/services",
    response_model=VisitorServicesResponse,
    responses={
        422: {
            "description": "The category query parameter failed validation.",
            "model": ValidationErrorResponse,
        },
        503: {
            "description": "The visitor-services dataset is unavailable.",
            "model": ErrorResponse,
        },
        500: {
            "description": "An unexpected visitor-services error occurred.",
            "model": ErrorResponse,
        },
    },
)
def get_visitor_services(
    category: ServiceCategory | None = Query(default=None),
) -> VisitorServicesResponse:
    """List visitor services, optionally filtered by category."""
    try:
        return find_visitor_services(category=category)
    except VisitorServicesDataError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The visitor-services dataset is unavailable.",
        ) from error
