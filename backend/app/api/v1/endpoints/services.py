
"""Visitor services API endpoints (Member 4)."""

from typing import Literal

from fastapi import APIRouter, Query

from backend.app.schemas.service import VisitorServicesResponse
from backend.app.services.visitor_services import find_visitor_services

router = APIRouter(tags=["Visitor Services"])

ServiceCategory = Literal["food", "market", "guide", "taxi", "other"]


@router.get("/services", response_model=VisitorServicesResponse)
def get_visitor_services(
    category: ServiceCategory | None = Query(default=None),
) -> VisitorServicesResponse:
    """List visitor services, optionally filtered by category."""
    return find_visitor_services(category=category)
