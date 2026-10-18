
import logging

from fastapi import APIRouter, HTTPException, status

from backend.app.ai.itinerary_generator import generate_itinerary
from backend.app.schemas.common import ErrorResponse
from backend.app.schemas.itinerary import (
    ItineraryRequest,
    ItineraryResponse,
)
from backend.app.services.itinerary_service import build_itinerary_response


router = APIRouter(tags=["Itinerary"])
logger = logging.getLogger(__name__)


@router.post(
    "/itinerary",
    response_model=ItineraryResponse,
    responses={
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Request validation failed.",
            "model": ErrorResponse,
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "Itinerary generation service unavailable.",
            "model": ErrorResponse,
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Unexpected itinerary generation error.",
            "model": ErrorResponse,
        },
    },
)
def create_itinerary(request: ItineraryRequest) -> ItineraryResponse:
    """Generate a heritage itinerary and calculate its estimated costs."""

    try:
        generated = generate_itinerary(request)

        daily_plans = generated["itinerary"]
        assumptions = generated.get("assumptions", [])

        result = build_itinerary_response(
            request=request,
            daily_plans=daily_plans,
            assumptions=assumptions,
        )

        return result

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    except RuntimeError as error:
        logger.exception("Itinerary generation service failed.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error

    except Exception as error:
        logger.exception("Unexpected itinerary endpoint error.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating the itinerary.",
        ) from error
