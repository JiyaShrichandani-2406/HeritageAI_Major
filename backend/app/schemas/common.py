"""Schemas shared by more than one module (owner: Member 1).

Feature-specific schemas (monument, place, route, chat, itinerary) stay in
their own files. Change this file only after agreeing with the team.
"""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    """Response of GET /api/v1/health (basic liveness check)."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["ok"] = Field(
        ...,
        description="'ok' when the API process is running.",
        examples=["ok"],
    )
    service: str = Field(
        ...,
        description="Name of the service.",
        examples=["heritageai-api"],
    )
    version: str = Field(
        ...,
        description="Version of the running API.",
        examples=["1.0.0"],
    )


class CostStatus(str, Enum):
    """How trustworthy a cost value is.

    Rule for every module: an unknown cost is null (None), never 0.
    """

    VERIFIED = "verified"
    ESTIMATED = "estimated"
    UNAVAILABLE = "unavailable"


class ErrorResponse(BaseModel):
    """Error body for failures such as 400, 404, 500 and 503."""

    detail: str = Field(..., examples=["Resource not found."])


class ValidationErrorItem(BaseModel):
    """One problem found while validating a request."""

    model_config = ConfigDict(extra="allow")

    loc: list[str | int]
    msg: str
    type: str


class ValidationErrorResponse(BaseModel):
    """Error body for 422 responses (invalid request data)."""

    detail: list[ValidationErrorItem]