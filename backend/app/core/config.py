"""Centralized API configuration using Pydantic settings.

This module defines `APISettings`, the single source of truth for runtime
configuration. Values are loaded from `backend/.env` (resolved relative to
this file) and environment variables. Key settings include:

- `API_PREFIX`: Mount path for OpenAPI and versioned routes.
- `ALLOWED_ORIGINS`: CORS origins (comma-separated). Default targets a local
    Vite dev server.
- `USE_RAG`: Feature flag to switch RAG usage by default.
- `MONGODB_*` / `MONGO_*`: Mongo connection URI and database name, supporting
    both naming schemes for flexibility across environments.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from pathlib import Path


class APISettings(BaseSettings):
    """Application settings with helpful defaults and fallbacks.

    The model loads from `backend/.env` and environment variables (case-insensitive).
    Use `get_settings()` to obtain a singleton instance throughout the app.
    """
    API_PREFIX: str = Field(default="/api")
    # Comma-separated list of allowed CORS origins. Prefer setting this in .env.
    # Default to local Vite dev server.
    ALLOWED_ORIGINS: str = Field(default="http://localhost:5173")
    # Feature flags
    USE_RAG: bool = Field(default=False)

    # Mongo (supports both names; prefer MONGODB_*; fallback to MONGO_*)
    MONGODB_URI: str | None = Field(default=None)
    MONGODB_DB_NAME: str = Field(default="asktube")

    MONGO_URI: str | None = Field(default=None)
    MONGO_DB_NAME: str | None = Field(default=None)

    # Resolve .env relative to the repository's backend folder so it loads
    # correctly regardless of the current working directory when the app starts.
    _ENV_PATH = Path(__file__).resolve().parents[2] / ".env"  # backend/.env
    model_config = SettingsConfigDict(env_file=str(_ENV_PATH), case_sensitive=False, extra="ignore")

    @property
    def mongo_uri(self) -> str | None:
        return self.MONGODB_URI or self.MONGO_URI

    @property
    def mongo_db_name(self) -> str:
        return self.MONGODB_DB_NAME or self.MONGO_DB_NAME or "asktube"


_settings: APISettings | None = None


def get_settings() -> APISettings:
    """Return a process-wide cached settings instance.

    Using a singleton avoids recomputing environment resolution on every import
    and provides a consistent configuration view.
    """
    global _settings
    if _settings is None:
        _settings = APISettings()
    return _settings
