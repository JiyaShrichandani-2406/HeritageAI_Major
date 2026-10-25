"""Central application configuration.

All settings are read from environment variables (optionally loaded from a
local ``.env`` file). Real environment variables always win over ``.env``.
No secrets are stored in this file.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

# backend/app/core/config.py -> parents[3] is the repository root.
PROJECT_ROOT = Path(__file__).resolve().parents[3]

VALID_ENVIRONMENTS = ("development", "test", "production")
DEFAULT_CORS_ORIGINS = "http://localhost:3000,http://localhost:5173"
DEFAULT_OLLAMA_URL = "http://localhost:11434/api/generate"


class ConfigError(RuntimeError):
    """Raised when the application configuration is invalid."""


@dataclass(frozen=True)
class Settings:
    """Validated, read-only application settings."""

    app_name: str
    service_name: str
    app_version: str
    environment: str
    cors_origins: tuple[str, ...]
    ollama_url: str
    ollama_model: str
    ollama_timeout_seconds: int
    data_dir: Path
    vector_store_dir: Path


def _get_str(name: str, default: str) -> str:
    """Return a stripped environment value, or the default if unset/blank."""
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return value.strip()


def _get_int(name: str, default: int, errors: list[str], minimum: int = 1) -> int:
    """Return an integer environment value, recording problems in errors."""
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = int(raw.strip())
    except ValueError:
        errors.append(f"{name} must be a whole number, but got {raw!r}.")
        return default
    if value < minimum:
        errors.append(f"{name} must be at least {minimum}, but got {value}.")
    return value


def _get_path(name: str, default: Path) -> Path:
    """Return a path; relative values are resolved from the project root."""
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    path = Path(raw.strip())
    return path if path.is_absolute() else (PROJECT_ROOT / path).resolve()


def load_settings() -> Settings:
    """Read, validate and return settings (reports every problem at once)."""
    load_dotenv(PROJECT_ROOT / ".env", override=False)

    errors: list[str] = []

    environment = _get_str("APP_ENV", "development").lower()
    if environment not in VALID_ENVIRONMENTS:
        errors.append(
            f"APP_ENV must be one of {', '.join(VALID_ENVIRONMENTS)}, "
            f"but got {environment!r}."
        )

    cors_origins = tuple(
        origin.strip()
        for origin in _get_str("CORS_ORIGINS", DEFAULT_CORS_ORIGINS).split(",")
        if origin.strip()
    )

    ollama_url = _get_str("OLLAMA_URL", DEFAULT_OLLAMA_URL)
    parsed_url = urlparse(ollama_url)
    if parsed_url.scheme not in ("http", "https") or not parsed_url.netloc:
        errors.append(
            f"OLLAMA_URL must be a full http(s) URL, but got {ollama_url!r}."
        )

    ollama_timeout = _get_int("OLLAMA_TIMEOUT_SECONDS", 600, errors)

    if errors:
        details = "\n".join(f"  - {message}" for message in errors)
        raise ConfigError(
            "Invalid configuration:\n"
            f"{details}\n"
            "Check your environment variables or the .env file "
            "(see .env.example)."
        )

    return Settings(
        app_name=_get_str("APP_NAME", "HeritageAI API"),
        service_name=_get_str("SERVICE_NAME", "heritageai-api"),
        app_version=_get_str("APP_VERSION", "1.0.0"),
        environment=environment,
        cors_origins=cors_origins,
        ollama_url=ollama_url,
        ollama_model=_get_str("OLLAMA_MODEL", "llama3.2"),
        ollama_timeout_seconds=ollama_timeout,
        data_dir=_get_path("DATA_DIR", PROJECT_ROOT / "data"),
        vector_store_dir=_get_path(
            "VECTOR_STORE_DIR", PROJECT_ROOT / "data" / "vector_store"
        ),
    )


@lru_cache
def get_settings() -> Settings:
    """Return the settings, loaded once and then cached."""
    return load_settings()