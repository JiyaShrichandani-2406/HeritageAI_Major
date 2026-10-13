
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ItineraryRequest(BaseModel):
    """Input accepted by POST /api/v1/itinerary."""

    model_config = ConfigDict(extra="forbid")

    destination: str = Field(
        ...,
        min_length=2,
        max_length=150,
        description="City or region where the traveler wants to explore heritage sites",
    )

    budget: float = Field(
        ...,
        gt=0,
        description="Total available trip budget in INR",
    )

    days: int = Field(
        ...,
        ge=1,
        le=30,
        description="Number of days for the trip",
    )

    interests: list[str] = Field(
        default_factory=list,
        max_length=20,
        description="Interests such as architecture, history, art, and culture",
    )

    travelers: int = Field(
        default=1,
        ge=1,
        le=100,
        description="Number of travelers",
    )

    travel_style: Literal["budget", "balanced", "comfortable"] = Field(
        default="budget",
        description="Preferred travel style",
    )

    include_food: bool = Field(
        default=True,
        description="Whether food expenses should be included",
    )

    include_transport: bool = Field(
        default=True,
        description="Whether local transport expenses should be included",
    )

    @model_validator(mode="after")
    def validate_interests(self):
        """Reject empty interest entries."""
        for interest in self.interests:
            if not interest.strip():
                raise ValueError("Interests cannot contain empty values.")
        return self


class ItineraryActivity(BaseModel):
    """One recommended activity or heritage stop."""

    model_config = ConfigDict(extra="forbid")

    place_name: str
    description: str
    estimated_entry_cost: float = Field(default=0, ge=0)
    estimated_transport_cost: float = Field(default=0, ge=0)
    estimated_food_cost: float = Field(default=0, ge=0)
    source_url: str | None = None


class ItineraryDay(BaseModel):
    """Activities and estimated expenses for one day."""

    day: int = Field(..., ge=1)
    title: str
    activities: list[ItineraryActivity] = Field(default_factory=list)
    estimated_cost: float = Field(..., ge=0)


class ItineraryResponse(BaseModel):
    """Output returned by POST /api/v1/itinerary."""

    model_config = ConfigDict(extra="forbid")

    destination: str
    days: int
    currency: str = "INR"
    itinerary: list[ItineraryDay] = Field(default_factory=list)
    estimated_total_cost: float = Field(..., ge=0)
    budget: float = Field(..., gt=0)
    within_budget: bool
    remaining_budget: float
    assumptions: list[str] = Field(default_factory=list)
    message: str
