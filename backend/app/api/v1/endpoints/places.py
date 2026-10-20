"""GET /api/v1/places/nearby (Member 3).

Member 1: in api/v1/router.py add
    api_router.include_router(places.router, prefix="/places", tags=["places"])
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.app.repositories.place_repository import PlacesDataError
from backend.app.schemas.common import ErrorResponse, ValidationErrorResponse
from backend.app.schemas.place import NearbyPlacesResponse, PlaceCategory
from backend.app.services.places_service import PlacesService, get_places_service

router = APIRouter()


@router.get(
    "/nearby",
    response_model=NearbyPlacesResponse,
    summary="Find nearby attractions",
    responses={
        422: {
            "description": "A query parameter failed validation.",
            "model": ValidationErrorResponse,
        },
        503: {
            "description": "The nearby-places dataset is unavailable.",
            "model": ErrorResponse,
        },
        500: {
            "description": "An unexpected nearby-places error occurred.",
            "model": ErrorResponse,
        },
    },
)
def nearby_places(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(10, gt=0, le=200),
    category: Optional[PlaceCategory] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    service: PlacesService = Depends(get_places_service),
) -> NearbyPlacesResponse:
    try:
        places = service.find_nearby(latitude, longitude, radius_km, category, limit)
    except PlacesDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    return NearbyPlacesResponse(count=len(places), places=places)
