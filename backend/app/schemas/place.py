"""Schemas for GET /api/v1/places/nearby (Member 3). Field names follow the team contract."""
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class PlaceCategory(str, Enum):
    monument = "monument"
    garden = "garden"
    museum = "museum"
    religious = "religious"
    nature = "nature"
    viewpoint = "viewpoint"
    market = "market"
    restaurant = "restaurant"


class NearbyPlacesQuery(BaseModel):
    """Query contract. The endpoint declares the same params with the same limits."""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    radius_km: float = Field(10, gt=0, le=200)
    category: Optional[PlaceCategory] = None
    limit: int = Field(10, ge=1, le=50)


class NearbyPlace(BaseModel):
    id: str
    name: str
    category: str
    latitude: float
    longitude: float
    address: str
    distance_km: float
    source_url: str


class NearbyPlacesResponse(BaseModel):
    count: int
    places: List[NearbyPlace]
