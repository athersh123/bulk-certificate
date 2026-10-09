from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Bulk Certificate Generation & Alert API"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "sqlite:///./bulk_certs.db"

    # Storage
    STORAGE_DIR: str = "./generated_certificates"
    MAX_BATCH_SIZE: int = 5000

    # Security
    API_KEY_ENABLED: bool = False
    API_KEY: Optional[str] = "secret-api-key-here"

    # Concurrency
    MAX_WORKER_CONCURRENCY: int = 5

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def storage_path(self) -> Path:
        path = Path(self.STORAGE_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()
