from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")
    database_url: str = "sqlite:///./data/soundwatch.db"
    jwt_secret: str = Field(min_length=32)
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:8080"]
    storage_dir: Path = Path("./data/storage")
    inference_mode: Literal["DEMO", "MODEL"] = "DEMO"
    model_path: str = ""
    model_name: str = "soundwatch-compatible-onnx"
    model_version: str = "1.0.0"
    confidence_threshold: float = Field(default=0.55, ge=0, le=1)
    max_upload_mb: int = Field(default=20, ge=1, le=100)
    max_duration_seconds: int = Field(default=120, ge=1, le=600)
    original_retention_days: int = Field(default=7, ge=1)
    result_retention_days: int = Field(default=90, ge=1)
    access_token_minutes: int = Field(default=60, ge=1)
    sample_rate: int = 16000


settings = Settings()
