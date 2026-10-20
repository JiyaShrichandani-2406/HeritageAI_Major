"""Pydantic schemas for visitor-services API endpoints (Member 4)."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ServiceCategory = Literal["food", "market", "guide", "taxi", "other"]
CostStatus = Literal["verified", "estimated", "unknown"]


class VisitorServiceResponse(BaseModel):
    """One visitor service returned by the API."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    category: ServiceCategory
    location: str
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    description: str
    estimated_cost: float | None = Field(default=None, ge=0)
    currency: str = "INR"
    cost_status: CostStatus
    source_url: str | None = None


class VisitorServicesResponse(BaseModel):
    """Filtered visitor services and a message about available data."""

    category: ServiceCategory | None = None
    services: list[VisitorServiceResponse] = Field(default_factory=list)
    message: str
