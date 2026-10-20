"""Domain model for a visitor service (Member 4)."""

from dataclasses import dataclass
from typing import Literal


ServiceCategory = Literal[
    "food",
    "market",
    "guide",
    "taxi",
    "other",
]


@dataclass(frozen=True)
class VisitorService:
    id: str
    name: str
    category: ServiceCategory
    location: str
    latitude: float | None
    longitude: float | None
    description: str
    estimated_cost: float | None
    currency: str
    cost_status: Literal["verified", "estimated", "unknown"]
    source_url: str | None
