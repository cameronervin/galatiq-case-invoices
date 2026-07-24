from functools import lru_cache
from pathlib import Path

from fastapi import Request
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="APP_",
        extra="ignore",
    )

    env: str = "local"
    log_level: str = "INFO"
    frontend_origin: str = "http://localhost:3000"
    database_path: Path = Path("inventory.db")
    upload_dir: Path = Path(".local/invoices")
    max_upload_bytes: int = Field(default=10 * 1024 * 1024, gt=0)
    default_currency: str = "USD"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
    celery_result_expires_seconds: int = Field(default=3600, ge=60)
    llm_provider: str = "offline"
    llm_model: str = "deterministic-v1"
    grok_model: str = "grok-4.5"
    xai_api_key: str | None = Field(default=None, validation_alias="XAI_API_KEY")
    workflow_timeout_seconds: int = Field(default=300, gt=0)

    @property
    def cors_origins(self) -> list[str]:
        return [self.frontend_origin, "http://127.0.0.1:3000"]


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_request_settings(request: Request) -> Settings:
    settings = getattr(request.app.state, "settings", None)
    if isinstance(settings, Settings):
        return settings
    return get_settings()
