"""Loader for the extended monument_visitor_info dataset.

The drop-in `heritage.json` schema can't carry entry fees or opening hours
without breaking the strict loader, so verified fees live in
`data/processed/extended/monument_visitor_info.json` keyed by catalog
`location_id` (e.g. `place-taj-mahal`). This repository exposes them to the
itinerary generator so activities show real prices instead of "Unknown".
"""

import json
from pathlib import Path
from typing import Any

_DATA_PATH = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "processed"
    / "extended"
    / "monument_visitor_info.json"
)

_cache: list[dict[str, Any]] | None = None


def _load() -> list[dict[str, Any]]:
    global _cache
    if _cache is None:
        if not _DATA_PATH.exists():
            _cache = []
        else:
            _cache = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
    return _cache


def _record_for(location_id: str) -> dict[str, Any] | None:
    for record in _load():
        if record.get("location_id") == location_id:
            return record
    return None


def get_entry_fee(
    location_id: str,
    visitor_type: str = "indian_adult",
) -> tuple[float | None, str, str | None]:
    """Return (amount_inr, cost_status, source_url) for a visitor category.

    ``cost_status`` is lowercase to match the drop-in convention used by the
    rest of the API (verified | estimated | unknown).
    """
    record = _record_for(location_id)
    if record is None:
        return None, "unknown", None

    for fee in record.get("entry_fees", []):
        if fee.get("category") == visitor_type:
            amount = fee.get("amount_inr")
            status = (fee.get("status") or "UNKNOWN").lower()
            if status == "not_applicable":
                return None, "unknown", None
            if status not in {"verified", "estimated", "unknown"}:
                status = "unknown"
            sources = fee.get("source_urls") or []
            source_url = sources[0] if sources else None
            return amount, status, source_url
    return None, "unknown", None


def get_guide_charges(location_id: str) -> dict[str, Any] | None:
    record = _record_for(location_id)
    if record is None:
        return None
    return record.get("guide_charges")
