"""Application configuration models and helpers."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import AliasChoices, Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["development", "test", "production"]


class Settings(BaseSettings):
    """Defines environment-backed settings used throughout the workspace."""

    app_name: str = "learnwithai"
    environment: Environment = "development"

    # Database
    database_url: str | None = None
    db_echo: bool = True

    # Queue / broker
    rabbitmq_url: str | None = None

    # App / API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"

    # Auth
    unc_auth_server_host: str = "csxl.unc.edu"
    host: str = "localhost:4200"
    jwt_secret: str = "reallysecuresecret-dev-default-key"
    jwt_algorithm: str = "HS256"

    # Static files
    static_dir: str = ""

    # OpenAI
    openai_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("AZURE_OPENAI_API_KEY", "OPENAI_API_KEY"),
    )
    openai_model: str = Field(
        default="gpt-5-mini",
        validation_alias=AliasChoices("AZURE_OPENAI_DEPLOYMENT", "OPENAI_MODEL"),
    )
    openai_endpoint: str = Field(
        default="https://azureaiapi.cloud.unc.edu",
        validation_alias=AliasChoices("AZURE_OPENAI_ENDPOINT", "OPENAI_ENDPOINT"),
    )
    openai_api_version: str = Field(
        default="2025-04-01-preview",
        validation_alias=AliasChoices("AZURE_OPENAI_API_VERSION", "OPENAI_API_VERSION"),
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @computed_field
    @property
    def effective_database_url(self) -> str:
        """Returns the configured database URL or the default for the environment."""
        if self.database_url:
            return self.database_url

        if self.environment == "test":
            return "postgresql+psycopg://postgres:postgres@postgres:5432/learnwithai_test"

        return "postgresql+psycopg://postgres:postgres@postgres:5432/learnwithai"

    @computed_field
    @property
    def effective_rabbitmq_url(self) -> str:
        """Returns the configured RabbitMQ URL or the default devcontainer URL."""
        if self.rabbitmq_url:
            return self.rabbitmq_url

        # Default for devcontainer / compose network
        return "amqp://guest:guest@rabbitmq:5672/"

    @computed_field
    @property
    def is_development(self) -> bool:
        """Reports whether the current environment is development."""
        return self.environment == "development"

    @computed_field
    @property
    def is_test(self) -> bool:
        """Reports whether the current environment is test."""
        return self.environment == "test"

    @computed_field
    @property
    def is_production(self) -> bool:
        """Reports whether the current environment is production."""
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Returns a cached settings instance for the current process."""
    return Settings()
