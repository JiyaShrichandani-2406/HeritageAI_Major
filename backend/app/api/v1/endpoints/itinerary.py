
from fastapi import APIRouter, HTTPException, status

from backend.app.ai.itinerary_generator import generate_itinerary
from backend.app.schemas.itinerary import (
    ItineraryRequest,
    ItineraryResponse,
)
from backend.app.services.itinerary_service import build_itinerary_response


router = APIRouter(prefix="/api/v1", tags=["Itinerary"])


@router.post("/itinerary", response_model=ItineraryResponse)
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
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The itinerary generation service is unavailable.",
        ) from error

    except Exception as error:
        print(f"Unexpected itinerary endpoint error: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating the itinerary.",
        ) from error
