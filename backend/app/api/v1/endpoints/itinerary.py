
import logging

from fastapi import APIRouter, HTTPException, status

from backend.app.ai.llm_client import OllamaTimeoutError
from backend.app.ai.itinerary_generator import (
    UnsupportedDestinationError,
    generate_itinerary,
)
from backend.app.schemas.common import (
    ErrorResponse,
    ValidationErrorResponse,
)
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
        422: {
            "description": (
                "The request body failed validation or the destination "
                "is not covered by the heritage catalog."
            ),
            "model": ValidationErrorResponse | ErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "days"],
                                "msg": "Input should be greater than or equal to 1",
                                "type": "greater_than_equal",
                            }
                        ]
                    }
                }
            },
        },
        502: {
            "description": "The AI service returned an invalid itinerary.",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "The AI must return exactly 2 daily plans."
                    }
                }
            },
        },
        503: {
            "description": "Itinerary generation service unavailable.",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "The itinerary generation service is unavailable."
                    }
                }
            },
        },
        504: {
            "description": "Ollama did not finish generating the itinerary in time.",
            "model": ErrorResponse,
        },
        500: {
            "description": "Unexpected itinerary generation error.",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "An unexpected error occurred while generating the itinerary."
                    }
                }
            },
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
            transport_options=generated.get("transport_options", []),
            visitor_services=generated.get("visitor_services", []),
        )

        return result

    except UnsupportedDestinationError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error

    except OllamaTimeoutError as error:
        logger.warning("Itinerary generation timed out: %s", error)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=str(error),
        ) from error

    except RuntimeError as error:
        logger.exception("Itinerary generation service failed.")
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error

    except Exception as error:
        logger.exception("Unexpected itinerary endpoint error.")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while generating the itinerary.",
        ) from error
