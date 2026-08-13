from functools import lru_cache
from typing import List, Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables or `.env`."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "SportsHub API"
    environment: Literal["development", "test", "production"] = "development"
    database_url: str = "postgresql+psycopg2://sportshub:sportshub_dev_password@localhost:5432/sportshub"
    secret_key: str = "development-only-change-me"
    access_token_expire_minutes: int = 30
    sports_provider: Literal["sample", "api-sports"] = "sample"
    api_sports_key: str = ""
    api_sports_base_url: str = "https://v3.football.api-sports.io"
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origin_list(self) -> List[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    def validate_runtime_safety(self) -> None:
        """Reject development credentials in a production configuration."""
        if self.environment == "production" and (
            self.secret_key == "development-only-change-me" or len(self.secret_key) < 32
        ):
            raise ValueError("SECRET_KEY must be at least 32 characters in production")


@lru_cache
def get_settings() -> Settings:
    return Settings()
