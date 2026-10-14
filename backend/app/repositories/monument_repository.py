"""Reads monument records from data/processed/heritage.json.

The project has no database layer yet, so records are loaded from the JSON file
once and cached. If a database is added later, only this file needs to change.
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

# backend/app/repositories/monument_repository.py -> repository root is parents[3]
HERITAGE_FILE = (
    Path(__file__).resolve().parents[3] / "data" / "processed" / "heritage.json"
)


@lru_cache(maxsize=1)
def _load_monuments() -> tuple[dict[str, Any], ...]:
    if not HERITAGE_FILE.exists():
        raise RuntimeError(f"Heritage data file not found: {HERITAGE_FILE}")

    with HERITAGE_FILE.open(encoding="utf-8") as file:
        records = json.load(file)

    if not isinstance(records, list):
        raise RuntimeError("heritage.json must contain a list of monuments.")

    return tuple(records)


def get_monument_by_id(monument_id: str) -> dict[str, Any] | None:
    wanted = monument_id.strip().lower()

    for record in _load_monuments():
        if record["id"].lower() == wanted:
            return record

    return None


def find_monument(query: str) -> dict[str, Any] | None:
    """Match free text such as 'Taj Mahal' or 'Agra' against id, name or city."""
    wanted = query.strip().lower()
    if not wanted:
        return None

    for record in _load_monuments():
        names = {
            record["id"].lower(),
            record["name"].lower(),
            record["city"].lower(),
        }
        if wanted in names:
            return record

    return None
