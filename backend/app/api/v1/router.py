"""Central versioned API router (owner: Member 1).

Every feature router is registered here, under the single /api/v1 prefix.
Feature routers must NOT define the /api/v1 prefix themselves.

Registered:
    health     -> Member 1
    chat       -> Member 5
    itinerary  -> Member 6

Planned (add each line only once the module exists and its tests pass):
    monuments  -> Member 2
    places     -> Member 3
    services   -> Member 4
    routes     -> Member 4
"""

from fastapi import APIRouter

from backend.app.api.v1.endpoints import chat, health, itinerary

API_V1_PREFIX = "/api/v1"

api_router = APIRouter(prefix=API_V1_PREFIX)

api_router.include_router(health.router)
api_router.include_router(chat.router)
api_router.include_router(itinerary.router)