from fastapi import APIRouter, HTTPException, status

from backend.app.repositories.location_repository import (
    LocationDataError,
    LocationRepository,
)
from backend.app.schemas.common import ErrorResponse
from backend.app.schemas.location import LocationCatalogResponse


router = APIRouter(tags=["Locations"])


@router.get(
    "/locations",
    response_model=LocationCatalogResponse,
    summary="List unified cities and places",
    responses={
        503: {
            "description": "A source location dataset is unavailable or malformed.",
            "model": ErrorResponse,
        },
    },
)
def list_locations() -> LocationCatalogResponse:
    try:
        repository = LocationRepository()
        return LocationCatalogResponse(
            cities=repository.cities(),
            places=repository.places(),
        )
    except LocationDataError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
