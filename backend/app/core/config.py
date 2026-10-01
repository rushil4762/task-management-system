from typing import List
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application Info
    APP_NAME: str = "Task Manager API"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = ""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/task_manager_db"
    DB_ECHO: bool = False

    # JWT Authentication
    JWT_SECRET_KEY: str = "your-super-secret-jwt-key-replace-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Task Reminders
    TASK_DUE_SOON_HOURS: int = 24

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return []

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.APP_ENV.lower() == "production":
            if (
                self.JWT_SECRET_KEY == "your-super-secret-jwt-key-replace-in-production"
                or len(self.JWT_SECRET_KEY) < 32
            ):
                raise ValueError(
                    "In production, JWT_SECRET_KEY must be a secure secret with at least 32 characters and cannot use the default placeholder."
                )
            if self.DEBUG:
                raise ValueError("DEBUG must be set to False in production.")
            if "*" in self.CORS_ORIGINS:
                raise ValueError(
                    "Wildcard '*' CORS origins are not permitted in production with credentials enabled."
                )
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
