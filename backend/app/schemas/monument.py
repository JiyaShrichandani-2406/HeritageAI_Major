from pydantic import BaseModel, ConfigDict, Field


class MonumentSource(BaseModel):
    """A reference used to verify the monument information."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=2, max_length=200)
    url: str = Field(..., min_length=8, max_length=500)


class MonumentImage(BaseModel):
    """An openly licensed image with the credit needed to display it."""

    model_config = ConfigDict(extra="forbid")

    url: str = Field(..., min_length=8, max_length=500)
    caption: str = Field(..., min_length=2, max_length=300)
    credit: str = Field(..., min_length=2, max_length=200)
    license: str = Field(..., min_length=2, max_length=100)


class MonumentResponse(BaseModel):
    """Output returned by GET /api/v1/monuments/{monument_id}."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    city: str
    state: str
    country: str
    summary: str
    history: str
    architecture: str
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    sources: list[MonumentSource] = Field(..., min_length=1)
    # Date the facts were last checked against the sources, e.g. "2026-10-20".
    # Left empty until someone has actually verified the record.
    last_verified: str | None = None
    # Not in the agreed schema yet. Optional so existing consumers are not broken.
    images: list[MonumentImage] = Field(default_factory=list)
