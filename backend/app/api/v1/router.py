
"""Central versioned API router (owner: Member 1)."""

from fastapi import APIRouter

from backend.app.api.v1.endpoints import (
    chat,
    health,
    itinerary,
    monuments,
    places,
)

API_V1_PREFIX = "/api/v1"

api_router = APIRouter(prefix=API_V1_PREFIX)

api_router.include_router(health.router)
api_router.include_router(chat.router)
api_router.include_router(itinerary.router)
api_router.include_router(monuments.router)
api_router.include_router(places.router, prefix="/places", tags=["Places"])
