"""Location-based filtering for nearby attractions (Member 3).

Member 6 (itinerary) and Member 5 (chat) can reuse this directly:
    from app.services.places_service import get_places_service
    places = get_places_service().find_nearby(27.1751, 78.0421, radius_km=15, category="garden", limit=5)
"""
from functools import lru_cache
from math import asin, cos, radians, sin, sqrt
from typing import List, Optional, Union

from app.repositories.place_repository import PlaceRepository
from app.schemas.place import NearbyPlace, PlaceCategory

EARTH_RADIUS_KM = 6371.0088


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometres."""
    d_lat, d_lon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * asin(sqrt(a))


class PlacesService:
    def __init__(self, repository: Optional[PlaceRepository] = None):
        self._repo = repository or PlaceRepository()

    def find_nearby(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 10,
        category: Optional[Union[PlaceCategory, str]] = None,
        limit: int = 10,
    ) -> List[NearbyPlace]:
        wanted = category.value if isinstance(category, PlaceCategory) else category
        results: List[NearbyPlace] = []
        for p in self._repo.all():
            if wanted and p.category != wanted:
                continue
            dist = haversine_km(latitude, longitude, p.latitude, p.longitude)
            if dist <= radius_km:
                results.append(NearbyPlace(**p.__dict__, distance_km=round(dist, 2)))
        results.sort(key=lambda x: (x.distance_km, x.name))
        return results[:limit]


@lru_cache(maxsize=1)
def get_places_service() -> PlacesService:
    return PlacesService()
