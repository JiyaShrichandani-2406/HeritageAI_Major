"""Read-only access to processed transport data (Member 4)."""

import json
import math
import os
from pathlib import Path

from backend.app.models.transport import TransportOption
from backend.app.repositories.location_repository import (
    LocationDataError,
    LocationRepository,
)


DEFAULT_DATA_PATH = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "processed"
    / "transport.json"
)


class TransportDataError(RuntimeError):
    """Raised when transport data is missing or malformed."""


def _validate_non_negative_number(
    value: object,
    field: str,
    route_id: str,
) -> float | None:
    if value is None:
        return None
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value < 0
    ):
        raise ValueError(
            f"Route {route_id!r} has invalid {field}; expected a "
            "non-negative number or null."
        )
    return float(value)


def _validate_duration(value: object, route_id: str) -> int | None:
    if value is None:
        return None
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 0
    ):
        raise ValueError(
            f"Route {route_id!r} has invalid estimated_duration_minutes; "
            "expected a non-negative integer or null."
        )
    return value


class TransportRepository:
    def __init__(self, data_path: Path | None = None):
        self._path = Path(
            data_path
            or os.getenv("TRANSPORT_DATA_PATH")
            or DEFAULT_DATA_PATH
        )
        self._options: list[TransportOption] | None = None

    def _load(self) -> list[TransportOption]:
        if self._options is None:
            try:
                raw = json.loads(self._path.read_text(encoding="utf-8-sig"))
                if not isinstance(raw, list):
                    raise ValueError("Expected a JSON list.")

                locations = LocationRepository()
                locations_by_id = {
                    location["id"]: location
                    for location in [*locations.cities(), *locations.places()]
                }
                options = []
                seen_route_ids: set[str] = set()
                for index, item in enumerate(raw, start=1):
                    if not isinstance(item, dict):
                        raise ValueError(
                            f"Route record {index} must be a JSON object."
                        )

                    route_id = item.get("id")
                    if not isinstance(route_id, str) or not route_id.strip():
                        raise ValueError(
                            f"Route record {index} has no valid ID."
                        )
                    route_id = route_id.strip()
                    if route_id in seen_route_ids:
                        raise ValueError(
                            f"Duplicate transport route ID {route_id!r}."
                        )
                    seen_route_ids.add(route_id)
                    origin_id = item.get("origin_id")
                    destination_id = item.get("destination_id")
                    if (
                        not isinstance(origin_id, str)
                        or not origin_id.strip()
                        or not isinstance(destination_id, str)
                        or not destination_id.strip()
                    ):
                        raise ValueError(
                            f"Route {route_id!r} must have origin_id and "
                            "destination_id."
                        )
                    origin_id = origin_id.strip()
                    destination_id = destination_id.strip()
                    if origin_id == destination_id:
                        raise ValueError(
                            f"Route {route_id!r} must connect different "
                            "locations."
                        )

                    origin = locations_by_id.get(origin_id)
                    destination = locations_by_id.get(destination_id)
                    if not origin or not destination:
                        raise ValueError(
                            f"Route {route_id} references "
                            "an unknown location ID."
                        )

                    cost_status = item.get("cost_status")
                    if cost_status not in {"verified", "estimated", "unknown"}:
                        raise ValueError(
                            f"Route {route_id!r} has invalid cost_status."
                        )
                    estimated_cost = _validate_non_negative_number(
                        item.get("estimated_cost"),
                        "estimated_cost",
                        route_id,
                    )
                    if (
                        (cost_status == "unknown" and estimated_cost is not None)
                        or (
                            cost_status in {"verified", "estimated"}
                            and estimated_cost is None
                        )
                    ):
                        raise ValueError(
                            f"Route {route_id!r} has a cost value that "
                            "conflicts with cost_status."
                        )

                    duration = _validate_duration(
                        item.get("estimated_duration_minutes"),
                        route_id,
                    )
                    duration_status = item.get(
                        "duration_status"
                    )
                    if duration_status not in {
                        "verified",
                        "estimated",
                        "unknown",
                    }:
                        raise ValueError(
                            f"Route {route_id!r} has invalid duration_status."
                        )
                    if (
                        (duration_status == "unknown" and duration is not None)
                        or (
                            duration_status in {"verified", "estimated"}
                            and duration is None
                        )
                    ):
                        raise ValueError(
                            f"Route {route_id!r} has a duration value that "
                            "conflicts with duration_status."
                        )

                    transport_type = item.get("transport_type")
                    if (
                        not isinstance(transport_type, str)
                        or not transport_type.strip()
                    ):
                        raise ValueError(
                            f"Route {route_id!r} has no valid transport_type."
                        )
                    currency = item.get("currency", "INR")
                    if not isinstance(currency, str) or not currency.strip():
                        raise ValueError(
                            f"Route {route_id!r} has no valid currency."
                        )
                    source_url = item.get("source_url")
                    if source_url is not None and not isinstance(source_url, str):
                        raise ValueError(
                            f"Route {route_id!r} has an invalid source_url."
                        )
                    notes = item.get("notes", "")
                    if not isinstance(notes, str):
                        raise ValueError(
                            f"Route {route_id!r} has invalid notes."
                        )
                    options.append(
                        TransportOption(
                            id=route_id,
                            origin_id=origin_id,
                            destination_id=destination_id,
                            origin=origin["name"],
                            destination=destination["name"],
                            transport_type=transport_type.strip(),
                            estimated_cost=estimated_cost,
                            currency=currency.strip(),
                            estimated_duration_minutes=duration,
                            duration_status=duration_status,
                            cost_status=cost_status,
                            source_url=source_url,
                            notes=notes,
                        )
                    )
                self._options = options
            except FileNotFoundError as exc:
                raise TransportDataError(
                    f"Transport data not found at {self._path}."
                ) from exc
            except LocationDataError as exc:
                raise TransportDataError(
                    "The location catalog required to resolve transport "
                    f"route IDs is unavailable: {exc}"
                ) from exc
            except (ValueError, TypeError, KeyError, OverflowError) as exc:
                raise TransportDataError(
                    f"Transport data at {self._path} is malformed: {exc}"
                ) from exc

        return self._options

    def all(self) -> list[TransportOption]:
        return list(self._load())

    def search(
        self,
        origin_id: str,
        destination_id: str,
    ) -> list[TransportOption]:
        """Return exact-direction city- or place-level route records."""
        if not isinstance(origin_id, str) or not origin_id.strip():
            raise ValueError("origin_id must be a non-empty location ID.")
        if not isinstance(destination_id, str) or not destination_id.strip():
            raise ValueError(
                "destination_id must be a non-empty location ID."
            )
        origin_id = origin_id.strip()
        destination_id = destination_id.strip()
        locations = LocationRepository()
        if not locations.get_location(origin_id):
            raise ValueError(f"Unknown origin location ID {origin_id!r}.")
        if not locations.get_location(destination_id):
            raise ValueError(
                f"Unknown destination location ID {destination_id!r}."
            )
        return [
            option
            for option in self._load()
            if option.origin_id == origin_id
            and option.destination_id == destination_id
        ]
