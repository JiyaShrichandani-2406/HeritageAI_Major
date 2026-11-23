"""Loader for extended transport-route details.

The drop-in `transport.json` carries just enough fields to validate against
the existing strict schema. Richer attributes (distance in km, fare category,
provider, booking URL, last_verified) live in
`data/processed/extended/transport_route_details.json`, keyed by the same
`route_id` the base dataset uses. This repository exposes them so the routes
endpoint can surface the extra context without changing the base loader.
"""

import json
from pathlib import Path
from typing import Any

_DATA_PATH = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "processed"
    / "extended"
    / "transport_route_details.json"
)

_cache: dict[str, dict[str, Any]] | None = None


def _load() -> dict[str, dict[str, Any]]:
    global _cache
    if _cache is None:
        if not _DATA_PATH.exists():
            _cache = {}
        else:
            raw = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
            _cache = {
                record["route_id"]: record
                for record in raw
                if isinstance(record, dict) and record.get("route_id")
            }
    return _cache


def get_route_details(route_id: str) -> dict[str, Any] | None:
    """Return the extended-detail record for a transport route, or None."""
    return _load().get(route_id)
