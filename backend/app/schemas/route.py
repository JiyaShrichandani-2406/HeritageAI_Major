"""Pydantic schemas for transport API endpoints (Member 4)."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


CostStatus = Literal["verified", "estimated", "unknown"]


class RouteRequest(BaseModel):
    """Request transport options between two locations."""

    model_config = ConfigDict(extra="forbid")

    origin: str = Field(..., min_length=2, max_length=150)
    destination: str = Field(..., min_length=2, max_length=150)

    @model_validator(mode="after")
    def validate_different_locations(self):
        if self.origin.strip().casefold() == self.destination.strip().casefold():
            raise ValueError("Origin and destination must be different.")
        return self


class TransportOptionResponse(BaseModel):
    """One transport option returned by the API."""

    id: str
    origin: str
    destination: str
    transport_type: str
    estimated_cost: float | None = Field(default=None, ge=0)
    currency: str = "INR"
    estimated_duration_minutes: int | None = Field(default=None, ge=0)
    cost_status: CostStatus
    source_url: str | None = None
    notes: str = ""


class RouteResponse(BaseModel):
    """Transport options and data limitations for a requested route."""

    origin: str
    destination: str
    options: list[TransportOptionResponse] = Field(default_factory=list)
    message: str
