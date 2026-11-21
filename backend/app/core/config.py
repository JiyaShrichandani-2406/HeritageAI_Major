
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

from dotenv import load_dotenv

# backend/app/core/config.py -> parents[3] is the repository root.
PROJECT_ROOT = Path(__file__).resolve().parents[3]

VALID_ENVIRONMENTS = ("development", "test", "production")
DEFAULT_CORS_ORIGINS = "http://localhost:3000,http://localhost:5173"



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

    # Cloudflare Workers AI settings
    cloudflare_account_id: str
    cloudflare_api_token: str
    cloudflare_text_model: str
    cloudflare_timeout_seconds: int



    data_dir: Path
    vector_store_dir: Path


def _get_str(name: str, default: str) -> str:
    """Return a stripped environment value, or the default if unset/blank."""
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return value.strip()


def _get_int(
    name: str,
    default: int,
    errors: list[str],
    minimum: int = 1,
) -> int:
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
        for origin in _get_str(
            "CORS_ORIGINS",
            DEFAULT_CORS_ORIGINS,
        ).split(",")
        if origin.strip()
    )

    # Cloudflare Workers AI configuration
    cloudflare_account_id = _get_str(
        "CLOUDFLARE_ACCOUNT_ID",
        "",
    )

    cloudflare_api_token = _get_str(
        "CLOUDFLARE_API_TOKEN",
        "",
    )

    cloudflare_text_model = _get_str(
        "CLOUDFLARE_TEXT_MODEL",
        "@cf/google/gemma-4-26b-a4b-it",
    )

    cloudflare_timeout = _get_int(
        "CLOUDFLARE_TIMEOUT_SECONDS",
        120,
        errors,
    )
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

        # Cloudflare
        cloudflare_account_id=cloudflare_account_id,
        cloudflare_api_token=cloudflare_api_token,
        cloudflare_text_model=cloudflare_text_model,
        cloudflare_timeout_seconds=cloudflare_timeout,
        data_dir=_get_path(
            "DATA_DIR",
            PROJECT_ROOT / "data",
        ),
        vector_store_dir=_get_path(
            "VECTOR_STORE_DIR",
            PROJECT_ROOT / "data" / "vector_store",
        ),
    )


@lru_cache
def get_settings() -> Settings:
    """Return the settings, loaded once and then cached."""
    return load_settings()
