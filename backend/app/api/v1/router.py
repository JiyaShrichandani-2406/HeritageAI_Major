"""Central versioned API router (owner: Member 1).

Every feature router is registered here, under the single /api/v1 prefix.
Feature routers must NOT define the /api/v1 prefix themselves.

Planned registrations (add each line only once the module exists and its
tests pass):
    monuments  -> Member 2
    places     -> Member 3
    services   -> Member 4
    routes     -> Member 4
    chat       -> Member 5
    itinerary  -> Member 6
"""

from fastapi import APIRouter

from backend.app.api.v1.endpoints import health

API_V1_PREFIX = "/api/v1"

api_router = APIRouter(prefix=API_V1_PREFIX)

api_router.include_router(health.router)