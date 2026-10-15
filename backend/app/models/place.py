"""Domain model for a nearby attraction (Member 3)."""
from dataclasses import dataclass

CATEGORIES = ("monument", "garden", "museum", "religious", "nature", "viewpoint")


@dataclass(frozen=True)
class Place:
    id: str
    name: str
    category: str
    latitude: float
    longitude: float
    address: str
    source_url: str
