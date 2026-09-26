"""Typed application settings loaded from environment variables / .env file
(project metadata, Postgres, Redis, JWT and rate-limit config). Import the
module-level `settings` singleton anywhere config values are needed.
"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Project metadata
    PROJECT_NAME: str
    API_V1_STR: str
    ENVIRONMENT: str
    DEBUG: bool

    # Database
    POSTGRES_SERVER: str
    POSTGRES_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DATABASE_URL: Optional[str] = None

    @property
    def sync_database_url(self) -> str:
        if self.DATABASE_URL:
            # Normalize to psycopg2 if needed
            if self.DATABASE_URL.startswith("postgres://"):
                return self.DATABASE_URL.replace("postgres://", "postgresql://", 1)
            return self.DATABASE_URL
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # Redis
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int
    REDIS_PASSWORD: Optional[str] = None

    # JWT & Cryptography
    SECRET_KEY: str = Field(
        description="HMAC secret key for JWT signing"
    )
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int

    # Rate Limiting
    RATE_LIMIT_LOGIN_PER_MINUTE: int
    RATE_LIMIT_REFRESH_PER_MINUTE: int


settings = Settings()
