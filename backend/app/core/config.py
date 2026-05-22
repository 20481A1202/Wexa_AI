from functools import lru_cache
from pydantic import field_validator
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Atlas Analytics"
    environment: str = "local"
    database_url: str = "sqlite+aiosqlite:///./analytics.db"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15
    refresh_token_days: int = 14
    frontend_origin: str = "http://localhost:5173"
    sendgrid_api_key: str | None = None
    sendgrid_from_email: str = "alerts@atlas.local"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+asyncpg://", 1)
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+asyncpg://", 1)
        return value

    @computed_field
    @property
    def frontend_origins(self) -> list[str]:
        origins = [origin.strip().rstrip("/") for origin in self.frontend_origin.split(",") if origin.strip()]
        defaults = ["http://localhost:3000", "http://localhost:5173"]
        return list(dict.fromkeys([*origins, *defaults]))


@lru_cache
def get_settings() -> Settings:
    return Settings()
