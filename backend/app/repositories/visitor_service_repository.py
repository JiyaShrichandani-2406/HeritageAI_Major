"""Read-only access to processed visitor services data (Member 4)."""

import json
import os
from pathlib import Path

from backend.app.models.visitor_service import VisitorService


DEFAULT_DATA_PATH = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "processed"
    / "visitor_services.json"
)


class VisitorServicesDataError(RuntimeError):
    """Raised when visitor-services data is missing or malformed."""


class VisitorServiceRepository:
    def __init__(self, data_path: Path | None = None):
        self._path = Path(
            data_path
            or os.getenv("VISITOR_SERVICES_DATA_PATH")
            or DEFAULT_DATA_PATH
        )
        self._services: list[VisitorService] | None = None

    def _load(self) -> list[VisitorService]:
        if self._services is None:
            try:
                raw = json.loads(
                    self._path.read_text(encoding="utf-8-sig")
                )
                if not isinstance(raw, list):
                    raise ValueError("Expected a JSON list.")

                self._services = [
                    VisitorService(**item) for item in raw
                ]
            except FileNotFoundError as exc:
                raise VisitorServicesDataError(
                    f"Visitor-services data not found at {self._path}."
                ) from exc
            except (ValueError, TypeError, KeyError) as exc:
                raise VisitorServicesDataError(
                    f"Visitor-services data at {self._path} "
                    f"is malformed: {exc}"
                ) from exc

        return self._services

    def all(self) -> list[VisitorService]:
        return list(self._load())

    def by_category(self, category: str) -> list[VisitorService]:
        category_key = category.casefold().strip()
        return [
            service
            for service in self._load()
            if service.category.casefold() == category_key
        ]
