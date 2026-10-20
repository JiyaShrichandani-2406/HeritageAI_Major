"""Domain model for a transport option (Member 4)."""

from dataclasses import dataclass
from typing import Literal


CostStatus = Literal["verified", "estimated", "unknown"]


@dataclass(frozen=True)
class TransportOption:
    id: str
    origin: str
    destination: str
    transport_type: str
    estimated_cost: float | None
    currency: str
    estimated_duration_minutes: int | None
    cost_status: CostStatus
    source_url: str | None
    notes: str = ""
