"""Pydantic schemas for transport API endpoints (Member 4)."""

from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

CostStatus = Literal["verified", "estimated", "unknown"]


class RouteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    origin_id: str = Field(..., min_length=3, max_length=150)
    destination_id: str = Field(..., min_length=3, max_length=150)

    @field_validator("origin_id", "destination_id")
    @classmethod
    def validate_location_not_blank(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Location ID must not be blank.")

        if len(value) < 3:
            raise ValueError("Location ID is invalid.")

        return value

    @model_validator(mode="after")
    def validate_different_locations(self):
        if self.origin_id == self.destination_id:
            raise ValueError("Origin and destination must be different.")
        return self


class TransportOptionResponse(BaseModel):
    """One transport option returned by the API."""

    id: str
    origin_id: str
    destination_id: str
    origin: str
    destination: str
    transport_type: str
    estimated_cost: float | None = Field(default=None, ge=0)
    currency: str = "INR"
    estimated_duration_minutes: int | None = Field(default=None, ge=0)
    duration_status: CostStatus
    cost_status: CostStatus
    source_url: str | None = None
    notes: str = ""


class RouteResponse(BaseModel):
    """Transport options and data limitations for a requested route."""

    origin_id: str
    destination_id: str
    origin: str
    destination: str
    options: list[TransportOptionResponse] = Field(default_factory=list)
    message: str
