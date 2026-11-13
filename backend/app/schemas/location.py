"""Schemas for the unified location catalog."""

from pydantic import BaseModel, ConfigDict, Field


class CityLocation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    state: str | None = None
    country: str | None = None
    aliases: list[str] = Field(default_factory=list)
    latitude: float | None = None
    longitude: float | None = None


class PlaceLocation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    city_id: str
    city: str
    state: str | None = None
    country: str | None = None
    category: str
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    coordinate_source: str
    address: str
    source_url: str | None = None
    source_urls: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)
    aliases: list[str] = Field(default_factory=list)


class LocationCatalogResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cities: list[CityLocation]
    places: list[PlaceLocation]
