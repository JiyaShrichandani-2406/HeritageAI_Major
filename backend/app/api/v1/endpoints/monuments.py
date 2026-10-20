from fastapi import APIRouter, HTTPException, status

from backend.app.schemas.common import ErrorResponse
from backend.app.schemas.monument import MonumentResponse
from backend.app.services.heritage_service import get_monument

router = APIRouter(tags=["Monuments"])


@router.get(
    "/monuments/{monument_id}",
    response_model=MonumentResponse,
    responses={
        404: {
            "description": "The requested monument does not exist.",
            "model": ErrorResponse,
        },
        503: {
            "description": "The heritage dataset is unavailable.",
            "model": ErrorResponse,
        },
        500: {
            "description": "An unexpected monument lookup error occurred.",
            "model": ErrorResponse,
        },
    },
)
def get_monument_details(monument_id: str) -> MonumentResponse:
    """Return the history, architecture and sources of a monument."""

    try:
        return get_monument(monument_id)

    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No monument found with id '{monument_id}'.",
        ) from error

    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The heritage data is unavailable.",
        ) from error

    except Exception as error:
        print(f"Unexpected monument endpoint error: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while loading the monument.",
        ) from error
