
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


CostStatus = Literal["verified", "estimated", "unknown"]


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

    entry_cost_status: CostStatus | None = None
    transport_cost_status: CostStatus | None = None
    food_cost_status: CostStatus | None = None

    source_url: str | None = None

    @model_validator(mode="before")
    @classmethod
    def infer_cost_statuses(cls, data):
        """Infer a safe default status when one is not supplied."""
        if not isinstance(data, dict):
            return data

        data = dict(data)

        status_fields = {
            "estimated_entry_cost": "entry_cost_status",
            "estimated_transport_cost": "transport_cost_status",
            "estimated_food_cost": "food_cost_status",
        }

        for cost_field, status_field in status_fields.items():
            if status_field not in data or data[status_field] is None:
                value = data.get(cost_field, 0)

                if (
                    isinstance(value, (int, float))
                    and not isinstance(value, bool)
                    and value > 0
                ):
                    data[status_field] = "estimated"
                else:
                    data[status_field] = "unknown"

        return data


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
