"""Merge heritage and nearby-place records into one location catalog."""

import json
import math
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_HERITAGE_PATH = ROOT / "data" / "processed" / "heritage.json"
DEFAULT_PLACES_PATH = ROOT / "data" / "processed" / "nearby_places.json"

_SOURCE_ID_ALIASES = {
    "guru-ka-taal-gurudwara": "guru-ka-taal",
    "mariam-tomb-sikandra": "tomb-mariam-uz-zamani",
}
_NAME_ALIASES = {
    "guru ka taal gurudwara": "guru-ka-taal",
    "soami bagh radhasoami samadhi": "soami-bagh-samadhi",
}
_CITY_ALIASES = {
    "sikandra agra": "Agra",
}
_EXTERNAL_CITY_NAMES = (
    "Delhi",
    "Bhopal",
)
_NEARBY_CITY_NAMES = ("Fatehpur Sikri", "Bharatpur", "Agra")
_EXTERNAL_CITY_DETAILS = {
    "Delhi": ("Delhi", "India"),
    "Bhopal": ("Madhya Pradesh", "India"),
}
_TRANSPORT_WAYPOINTS = (
    {
        "id": "place-fatehpur-sikri-parking-area",
        "name": "Fatehpur Sikri parking area",
        "city_id": "city-fatehpur-sikri",
        "city": "Fatehpur Sikri",
        "state": "Uttar Pradesh",
        "country": "India",
        "category": "transit_stop",
        "latitude": None,
        "longitude": None,
        "coordinate_source": "unavailable",
        "address": "Fatehpur Sikri, Uttar Pradesh",
        "source_url": "https://agra.nic.in/tourist-place/fatehpur-sikri/",
        "source_urls": [
            "https://agra.nic.in/tourist-place/fatehpur-sikri/"
        ],
        "source_ids": ["transport:fatehpur-sikri-parking-battery-bus"],
        "aliases": [],
    },
    {
        "id": "place-fatehpur-sikri-monument-gate",
        "name": "Fatehpur Sikri monument gate",
        "city_id": "city-fatehpur-sikri",
        "city": "Fatehpur Sikri",
        "state": "Uttar Pradesh",
        "country": "India",
        "category": "transit_stop",
        "latitude": None,
        "longitude": None,
        "coordinate_source": "unavailable",
        "address": "Fatehpur Sikri, Uttar Pradesh",
        "source_url": "https://agra.nic.in/tourist-place/fatehpur-sikri/",
        "source_urls": [
            "https://agra.nic.in/tourist-place/fatehpur-sikri/"
        ],
        "source_ids": ["transport:fatehpur-sikri-parking-battery-bus"],
        "aliases": [],
    },
)


class LocationDataError(RuntimeError):
    """Raised when source location data cannot form a consistent catalog."""


def _normalized(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def _canonical_source_id(source_id: str) -> str:
    return _SOURCE_ID_ALIASES.get(source_id, source_id)


def _name_keys(name: str) -> set[str]:
    name_parts = [name.split("(", maxsplit=1)[0].strip(), name]
    name_parts.extend(re.findall(r"\(([^)]+)\)", name))
    keys = {_normalized(part) for part in name_parts if part.strip()}
    return keys | {_NAME_ALIASES[key] for key in keys if key in _NAME_ALIASES}


def _read_records(
    path: Path,
    label: str,
    required_fields: tuple[str, ...],
) -> list[dict[str, Any]]:
    try:
        records = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as error:
        raise LocationDataError(
            f"Unable to read {label} location data at {path}: {error}"
        ) from error

    if not isinstance(records, list) or not all(
        isinstance(record, dict) for record in records
    ):
        raise LocationDataError(f"{label} location data must be a JSON list.")
    if not records:
        raise LocationDataError(f"{label} location data cannot be empty.")

    for index, record in enumerate(records, start=1):
        missing_fields = [
            field
            for field in required_fields
            if field not in record
            or record[field] is None
            or (
                isinstance(record[field], str)
                and not record[field].strip()
            )
        ]
        if missing_fields:
            raise LocationDataError(
                f"{label} location record {index} is missing: "
                f"{', '.join(missing_fields)}."
            )
        if label == "heritage" and (
            not isinstance(record["sources"], list)
            or not all(isinstance(source, dict) for source in record["sources"])
        ):
            raise LocationDataError(
                f"Heritage location record {index} has invalid sources."
            )

    return records


def _heritage_city(record: dict[str, Any]) -> str:
    city = str(record.get("city") or "").strip()
    if not city:
        raise LocationDataError(
            f"Heritage record {record.get('id', '<unknown>')} has no city."
        )

    normalized_city = _normalized(city)
    return _CITY_ALIASES.get(normalized_city, city)


def _nearby_city(
    record: dict[str, Any],
    known_city_names: tuple[str, ...] = _NEARBY_CITY_NAMES,
) -> str:
    address = str(record.get("address") or "")
    address_key = _normalized(address)
    for city_name in sorted(
        known_city_names,
        key=lambda name: len(_normalized(name)),
        reverse=True,
    ):
        if _normalized(city_name) in address_key:
            return city_name

    raise LocationDataError(
        f"Nearby place {record.get('id', '<unknown>')} has no recognized city "
        f"in address {address!r}."
    )


def _state_country(
    heritage_record: dict[str, Any] | None,
    city_name: str,
) -> tuple[str | None, str | None]:
    if heritage_record:
        return heritage_record.get("state"), heritage_record.get("country")

    if city_name == "Bharatpur":
        return "Rajasthan", "India"
    if city_name in {"Agra", "Fatehpur Sikri"}:
        return "Uttar Pradesh", "India"
    return None, None


def _location_id(kind: str, source_id: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", source_id.casefold()).strip("-")
    return f"{kind}-{slug}"


def _build_catalog(
    heritage_records: list[dict[str, Any]],
    nearby_records: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    heritage_by_source_id = {
        str(record["id"]): record for record in heritage_records
    }
    if len(heritage_by_source_id) != len(heritage_records):
        raise LocationDataError("heritage.json contains duplicate location IDs.")

    nearby_by_source_id = {
        str(record["id"]): record for record in nearby_records
    }
    if len(nearby_by_source_id) != len(nearby_records):
        raise LocationDataError(
            "nearby_places.json contains duplicate location IDs."
        )

    heritage_by_id: dict[str, dict[str, Any]] = {}
    heritage_by_name: dict[str, list[dict[str, Any]]] = {}
    for record in heritage_records:
        source_id = str(record["id"])
        heritage_by_id[_canonical_source_id(source_id)] = record
        for name_key in _name_keys(str(record["name"])):
            matches = heritage_by_name.setdefault(name_key, [])
            if record not in matches:
                matches.append(record)

    known_city_names = tuple(
        {
            *_NEARBY_CITY_NAMES,
            *_EXTERNAL_CITY_NAMES,
            *(_heritage_city(record) for record in heritage_records),
        }
    )
    merged: dict[str, dict[str, Any]] = {}
    for record in heritage_records:
        source_id = str(record["id"])
        key = _canonical_source_id(source_id)
        if key in merged:
            raise LocationDataError(
                f"Multiple heritage records resolve to location {key!r}."
            )
        merged[key] = {
            "heritage": record,
            "nearby": None,
            "source_ids": [f"heritage:{source_id}"],
            "aliases": [str(record["name"])],
        }
    for record in nearby_records:
        source_id = str(record["id"])
        canonical_id = _canonical_source_id(source_id)
        nearby_city = _nearby_city(record, known_city_names)
        heritage_match = heritage_by_id.get(canonical_id)
        if heritage_match is None:
            name_matches: dict[str, dict[str, Any]] = {}
            for name_key in _name_keys(str(record["name"])):
                for candidate in heritage_by_name.get(name_key, []):
                    if _heritage_city(candidate).casefold() == nearby_city.casefold():
                        name_matches[str(candidate["id"])] = candidate
            if len(name_matches) > 1:
                raise LocationDataError(
                    f"Nearby place {source_id!r} has an ambiguous heritage match."
                )
            heritage_match = next(iter(name_matches.values()), None)
        if heritage_match:
            key = _canonical_source_id(str(heritage_match["id"]))
            if _heritage_city(heritage_match).casefold() != nearby_city.casefold():
                raise LocationDataError(
                    f"Location {source_id!r} has conflicting city assignments."
                )
        else:
            key = canonical_id

        if key not in merged:
            merged[key] = {
                "heritage": None,
                "nearby": None,
                "source_ids": [],
                "aliases": [],
            }

        item = merged[key]
        if item["nearby"] is not None:
            raise LocationDataError(
                f"Multiple nearby records resolve to location {key!r}."
            )
        item["nearby"] = record
        item["source_ids"].append(f"nearby:{source_id}")
        for alias in (str(record["name"]),):
            if alias not in item["aliases"]:
                item["aliases"].append(alias)

    cities: dict[str, dict[str, Any]] = {}
    places: list[dict[str, Any]] = []
    seen_place_ids: set[str] = set()

    for key, item in merged.items():
        heritage_record = item["heritage"]
        nearby_record = item["nearby"]
        canonical_name = str(
            (heritage_record or nearby_record)["name"]
        ).strip()

        if heritage_record:
            city_name = _heritage_city(heritage_record)
        else:
            city_name = _nearby_city(nearby_record, known_city_names)

        city_key = _normalized(city_name)
        city_id = _location_id("city", city_key)
        state, country = _state_country(
            heritage_record,
            city_name,
        )
        city = cities.setdefault(
            city_id,
            {
                "id": city_id,
                "name": city_name,
                "state": state,
                "country": country,
                "aliases": [],
                "latitude": None,
                "longitude": None,
            },
        )
        if (
            city["state"]
            and state
            and city["state"].casefold() != state.casefold()
        ):
            raise LocationDataError(
                f"City {city_name!r} has conflicting state assignments."
            )
        if heritage_record:
            raw_city = str(heritage_record["city"]).strip()
            if raw_city != city_name and raw_city not in city["aliases"]:
                city["aliases"].append(raw_city)

        place_id = _location_id("place", key)
        if place_id in seen_place_ids or place_id in cities:
            raise LocationDataError(
                f"Location ID {place_id!r} is not unique."
            )
        seen_place_ids.add(place_id)

        coordinates = nearby_record or heritage_record
        latitude = coordinates.get("latitude")
        longitude = coordinates.get("longitude")
        if (
            isinstance(latitude, bool)
            or isinstance(longitude, bool)
            or not isinstance(latitude, (int, float))
            or not isinstance(longitude, (int, float))
            or not math.isfinite(latitude)
            or not math.isfinite(longitude)
            or not -90 <= latitude <= 90
            or not -180 <= longitude <= 180
        ):
            raise LocationDataError(
                f"Location {canonical_name!r} has invalid coordinates."
            )

        heritage_sources = [
            source.get("url")
            for source in (heritage_record or {}).get("sources", [])
            if source.get("url")
        ]
        nearby_source = (nearby_record or {}).get("source_url")
        source_urls = list(
            dict.fromkeys(
                ([nearby_source] if nearby_source else []) + heritage_sources
            )
        )
        aliases = list(dict.fromkeys(item["aliases"]))
        if canonical_name not in aliases:
            aliases.insert(0, canonical_name)

        places.append(
            {
                "id": place_id,
                "name": canonical_name,
                "city_id": city_id,
                "city": city_name,
                "state": state,
                "country": country,
                "category": (nearby_record or {}).get("category", "monument"),
                "latitude": latitude,
                "longitude": longitude,
                "coordinate_source": (
                    "nearby_places.json"
                    if nearby_record
                    else "heritage.json"
                ),
                "address": (nearby_record or {}).get(
                    "address",
                    f"{city_name}, {state}, {country}",
                ),
                "source_url": source_urls[0] if source_urls else None,
                "source_urls": source_urls,
                "source_ids": item["source_ids"],
                "aliases": aliases,
            }
        )

    for city_name, (state, country) in _EXTERNAL_CITY_DETAILS.items():
        city_id = _location_id("city", _normalized(city_name))
        cities.setdefault(
            city_id,
            {
                "id": city_id,
                "name": city_name,
                "state": state,
                "country": country,
                "aliases": [],
                "latitude": None,
                "longitude": None,
            },
        )

    places.extend(
        waypoint
        for waypoint in _TRANSPORT_WAYPOINTS
        if waypoint["city_id"] in cities
    )

    all_ids = set(cities)
    for place in places:
        if place["id"] in all_ids:
            raise LocationDataError(
                f"Location ID {place['id']!r} is not unique."
            )
        all_ids.add(place["id"])
        if place["city_id"] not in cities:
            raise LocationDataError(
                f"Place {place['id']!r} references an unknown city."
            )

    return {
        "cities": sorted(cities.values(), key=lambda city: city["name"].casefold()),
        "places": sorted(places, key=lambda place: place["name"].casefold()),
    }


@lru_cache(maxsize=4)
def _load_catalog(
    heritage_path: str,
    nearby_path: str,
) -> tuple[tuple[dict[str, Any], ...], tuple[dict[str, Any], ...]]:
    catalog = _build_catalog(
        _read_records(
            Path(heritage_path),
            "heritage",
            (
                "id",
                "name",
                "city",
                "state",
                "country",
                "latitude",
                "longitude",
                "sources",
            ),
        ),
        _read_records(
            Path(nearby_path),
            "nearby-place",
            (
                "id",
                "name",
                "address",
                "category",
                "latitude",
                "longitude",
                "source_url",
            ),
        ),
    )
    return tuple(catalog["cities"]), tuple(catalog["places"])


class LocationRepository:
    def __init__(
        self,
        heritage_path: Path | None = None,
        nearby_path: Path | None = None,
    ):
        self._heritage_path = Path(
            heritage_path
            or os.getenv("HERITAGE_DATA_PATH")
            or DEFAULT_HERITAGE_PATH
        )
        self._nearby_path = Path(
            nearby_path
            or os.getenv("PLACES_DATA_PATH")
            or DEFAULT_PLACES_PATH
        )

    def cities(self) -> list[dict[str, Any]]:
        return list(_load_catalog(
            str(self._heritage_path),
            str(self._nearby_path),
        )[0])

    def places(self) -> list[dict[str, Any]]:
        return list(_load_catalog(
            str(self._heritage_path),
            str(self._nearby_path),
        )[1])

    def find_city(self, name: str) -> dict[str, Any] | None:
        wanted = _normalized(name)
        return next(
            (
                city
                for city in self.cities()
                if wanted == _normalized(city["name"])
                or wanted in {_normalized(alias) for alias in city["aliases"]}
            ),
            None,
        )

    def find_place(self, name: str) -> dict[str, Any] | None:
        wanted = _name_keys(name)
        return next(
            (
                place
                for place in self.places()
                if wanted.intersection(
                    key
                    for alias in [place["name"], *place["aliases"]]
                    for key in _name_keys(alias)
                )
            ),
            None,
        )

    def get_location(self, location_id: str) -> dict[str, Any] | None:
        return next(
            (
                location
                for location in [*self.cities(), *self.places()]
                if location["id"] == location_id
            ),
            None,
        )
