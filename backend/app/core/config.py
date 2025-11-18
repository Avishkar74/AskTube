from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from pathlib import Path


class APISettings(BaseSettings):
    API_PREFIX: str = Field(default="/api")
    ALLOWED_ORIGINS: str = Field(default="*")
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
    global _settings
    if _settings is None:
        _settings = APISettings()
    return _settings
