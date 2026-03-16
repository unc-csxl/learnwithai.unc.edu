from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


Environment = Literal["development", "test", "production"]


class Settings(BaseSettings):
    app_name: str = "learnwithai"
    environment: Environment = "development"

    # Database
    database_url: str | None = None
    db_echo: bool = False

    # Queue / broker
    rabbitmq_url: str | None = None

    # App / API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"

    # Auth
    unc_auth_server_host: str = "csxl.unc.edu"
    host: str = "localhost:8000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @computed_field
    @property
    def effective_database_url(self) -> str:
        if self.database_url:
            return self.database_url

        if self.environment == "test":
            return (
                "postgresql+psycopg://postgres:postgres@postgres:5432/learnwithai_test"
            )

        return "postgresql+psycopg://postgres:postgres@postgres:5432/learnwithai"

    @computed_field
    @property
    def effective_rabbitmq_url(self) -> str:
        if self.rabbitmq_url:
            return self.rabbitmq_url

        # Default for devcontainer / compose network
        return "amqp://guest:guest@rabbitmq:5672/"

    @computed_field
    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    @computed_field
    @property
    def is_test(self) -> bool:
        return self.environment == "test"

    @computed_field
    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
