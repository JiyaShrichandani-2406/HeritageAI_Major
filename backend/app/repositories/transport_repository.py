"""Read-only access to processed transport data (Member 4)."""

import json
import os
from pathlib import Path

from backend.app.models.transport import TransportOption


DEFAULT_DATA_PATH = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "processed"
    / "transport.json"
)


class TransportDataError(RuntimeError):
    """Raised when transport data is missing or malformed."""


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

                self._options = [TransportOption(**item) for item in raw]
            except FileNotFoundError as exc:
                raise TransportDataError(
                    f"Transport data not found at {self._path}."
                ) from exc
            except (ValueError, TypeError, KeyError) as exc:
                raise TransportDataError(
                    f"Transport data at {self._path} is malformed: {exc}"
                ) from exc

        return self._options

    def all(self) -> list[TransportOption]:
        return list(self._load())

    def search(self, origin: str, destination: str) -> list[TransportOption]:
        origin_key = origin.casefold().strip()
        destination_key = destination.casefold().strip()

        return [
            option
            for option in self._load()
            if option.origin.casefold().strip() == origin_key
            and option.destination.casefold().strip() == destination_key
        ]

