"""Read-only access to data/processed/nearby_places.json (Member 3).

No dependency on the shared DB layer, so it works before and after Member 1's db/ is ready.
Override the file location with env var PLACES_DATA_PATH.
"""
import json
import os
from pathlib import Path
from typing import List, Optional

from backend.app.models.place import Place

# backend/app/repositories/place_repository.py -> repo root is parents[3]
DEFAULT_DATA_PATH = Path(__file__).resolve().parents[3] / "data" / "processed" / "nearby_places.json"


class PlacesDataError(RuntimeError):
    """Raised when the places dataset is missing or malformed."""


class PlaceRepository:
    def __init__(self, data_path: Optional[Path] = None):
        self._path = Path(data_path or os.getenv("PLACES_DATA_PATH") or DEFAULT_DATA_PATH)
        self._places: Optional[List[Place]] = None

    def _load(self) -> List[Place]:
        if self._places is None:
            try:
                raw = json.loads(self._path.read_text(encoding="utf-8"))
                self._places = [Place(**item) for item in raw]
            except FileNotFoundError as exc:
                raise PlacesDataError(
                    f"Places data not found at {self._path}. Run: python -m app.ingestion.import_places"
                ) from exc
            except (ValueError, TypeError) as exc:
                raise PlacesDataError(f"Places data at {self._path} is malformed: {exc}") from exc
        return self._places

    def all(self) -> List[Place]:
        return list(self._load())

    def get(self, place_id: str) -> Optional[Place]:
        return next((p for p in self._load() if p.id == place_id), None)
