"""Health endpoint (owner: Member 1).

This is a basic liveness check: it only proves the API process is running.
It must never depend on Ollama, vector stores or other external services.
"""

from fastapi import APIRouter

from backend.app.core.config import get_settings
from backend.app.schemas.common import HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="API liveness check",
)
def get_health() -> HealthResponse:
    """Return the service name and version when the API is running."""
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service=settings.service_name,
        version=settings.app_version,
    )