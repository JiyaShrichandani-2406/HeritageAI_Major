"""GET /api/v1/places/nearby (Member 3).

Member 1: in api/v1/router.py add
    api_router.include_router(places.router, prefix="/places", tags=["places"])
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.repositories.place_repository import PlacesDataError
from app.schemas.place import NearbyPlacesResponse, PlaceCategory
from app.services.places_service import PlacesService, get_places_service

router = APIRouter()


@router.get("/nearby", response_model=NearbyPlacesResponse, summary="Find nearby attractions")
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
        raise HTTPException(status_code=503, detail=str(exc))
    return NearbyPlacesResponse(count=len(places), places=places)
