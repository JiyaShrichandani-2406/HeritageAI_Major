
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from backend.app.schemas.route import TransportOptionResponse
from backend.app.schemas.service import VisitorServiceResponse


CostStatus = Literal["verified", "estimated", "unknown"]


class ItineraryRequest(BaseModel):
    """Input accepted by POST /api/v1/itinerary."""

    model_config = ConfigDict(extra="forbid")

    itinerary_mode: Literal["city_to_city", "place_to_place"] | None = Field(
        default=None,
        description="Optional itinerary mode. Omitted for legacy destination planning.",
    )

    destination: str = Field(
        ...,
        min_length=2,
        max_length=150,
        description="Destination city, region, or selected heritage place",
    )

    origin: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
        description="Starting city or place; required when an itinerary mode is selected",
    )

    origin_id: str | None = Field(
        default=None,
        min_length=3,
        max_length=150,
        description="Canonical city or place ID used to look up transport routes",
    )

    destination_id: str | None = Field(
        default=None,
        min_length=3,
        max_length=150,
        description="Canonical destination city or place ID used to look up routes",
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

    include_guides: bool = Field(
        default=False,
        description="Whether sourced guide costs should be included",
    )

    include_parking: bool = Field(
        default=False,
        description="Whether vehicle parking costs should be included",
    )

    parking_vehicle_type: Literal[
        "two_wheeler",
        "car_taxi",
        "tempo_traveller",
        "bus",
    ] | None = Field(
        default=None,
        description="Vehicle category used to select a sourced parking estimate",
    )

    @field_validator("destination", "origin", mode="before")
    @classmethod
    def strip_locations(cls, value):
        """Trim locations before applying their length and equality checks."""
        return value.strip() if isinstance(value, str) else value

    @field_validator("origin_id", "destination_id", mode="before")
    @classmethod
    def strip_location_ids(cls, value):
        """Trim canonical IDs before applying their length constraints."""
        return value.strip() if isinstance(value, str) else value

    def _validate_city_to_city_request(self) -> None:
        if self.destination.casefold() != "agra":
            raise ValueError(
                "City-to-city itineraries must use Agra as the destination."
            )
        self.destination = "Agra"
        if not self.origin:
            raise ValueError(
                "City-to-city itineraries require an origin city."
            )

    def _validate_place_to_place_request(self) -> None:
        if not self.origin:
            raise ValueError(
                "Place-to-place itineraries require a starting place."
            )

    @model_validator(mode="after")
    def validate_request(self):
        """Validate interests and enforce mode-specific location requirements."""
        for interest in self.interests:
            if not interest.strip():
                raise ValueError("Interests cannot contain empty values.")
        if self.itinerary_mode == "city_to_city":
            self._validate_city_to_city_request()
        elif self.itinerary_mode == "place_to_place":
            self._validate_place_to_place_request()
        if self.include_parking and self.parking_vehicle_type is None:
            raise ValueError(
                "A vehicle type is required when parking costs are included."
            )
        if not self.include_parking and self.parking_vehicle_type is not None:
            raise ValueError(
                "A parking vehicle type can only be set when parking costs "
                "are included."
            )
        if (
            self.origin
            and self.origin.strip().casefold()
            == self.destination.strip().casefold()
        ):
            raise ValueError("Origin and destination must be different.")
        return self


class ItineraryActivity(BaseModel):
    """One recommended activity or heritage stop."""

    model_config = ConfigDict(extra="forbid")

    place_name: str
    description: str
    estimated_entry_cost: float | None = Field(
        default=None,
        ge=0,
        description="Entry cost in INR, or null if unknown.",
    )
    estimated_transport_cost: float | None = Field(
        default=None,
        ge=0,
        description="Transport cost in INR, or null if unknown.",
    )
    estimated_travel_duration_minutes: int | None = Field(
        default=None,
        ge=0,
        description="Sourced travel duration from the previous stop, if available.",
    )
    travel_duration_status: CostStatus = "unknown"
    transport_type: str | None = None
    transport_source_url: str | None = None
    transport_notes: str | None = None
    estimated_food_cost: float | None = Field(
        default=None,
        ge=0,
        description="Food cost in INR, or null if unknown.",
    )

    estimated_guide_cost: float | None = Field(default=None, ge=0)
    guide_cost_status: CostStatus = "unknown"
    guide_source_url: str | None = None
    estimated_parking_cost: float | None = Field(default=None, ge=0)
    parking_cost_status: CostStatus = "unknown"
    parking_source_url: str | None = None

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
            "estimated_guide_cost": "guide_cost_status",
            "estimated_parking_cost": "parking_cost_status",
        }

        for cost_field, status_field in status_fields.items():
            if status_field not in data or data[status_field] is None:
                value = data.get(cost_field)

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
    activities: list[ItineraryActivity] = Field(
        default_factory=list,
        min_length=1,
        max_length=4,
    )
    estimated_cost: float | None = Field(
        ...,
        ge=0,
        description="Estimated day total, or null if an included cost is unknown.",
    )


class ItineraryResponse(BaseModel):
    """Output returned by POST /api/v1/itinerary."""

    model_config = ConfigDict(extra="forbid")

    destination: str
    days: int
    currency: str = "INR"
    itinerary: list[ItineraryDay] = Field(default_factory=list)
    transport_options: list[TransportOptionResponse] = Field(
        default_factory=list,
        description=(
            "Matching route options; selected route costs are reflected in "
            "activity estimates when applicable."
        ),
    )
    visitor_services: list[VisitorServiceResponse] = Field(
        default_factory=list,
        description=(
            "Matching visitor-service records; selected guide or parking "
            "costs are reflected in activity estimates when applicable."
        ),
    )
    known_cost_subtotal: float = Field(
        ...,
        ge=0,
        description="Sum of known included costs; may be incomplete.",
    )
    priced_cost_subtotal: float = Field(
        ...,
        ge=0,
        description=(
            "Sum of verified and estimated included costs; excludes unknown "
            "costs and is not a complete total when any are unknown."
        ),
    )
    unknown_cost_count: int = Field(
        ...,
        ge=0,
        description="Number of included cost categories with unknown amounts.",
    )
    estimated_total_cost: float | None = Field(
        ...,
        ge=0,
        description="Complete estimated total, or null if included costs are unknown.",
    )
    budget: float = Field(..., gt=0)
    within_budget: bool | None = Field(
        ...,
        description=(
            "True if within budget, false if over budget, "
            "or null if included estimates or unknown costs prevent "
            "verified budget compliance."
        ),
    )
    remaining_budget: float | None = Field(
        ...,
        description="Remaining budget, or null when the total cost is incomplete.",
    )
    assumptions: list[str] = Field(default_factory=list)
    message: str
