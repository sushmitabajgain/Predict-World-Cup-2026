from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "World Cup Predictor"
    environment: str = "development"
    database_url: str = Field(
        default="postgresql+psycopg2://worldcup:worldcup@postgres:5432/worldcup"
    )
    redis_url: str = "redis://redis:6379/0"
    mlflow_tracking_uri: str = "http://mlflow:5000"
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ]
    model_dir: Path = Path("app/ml/artifacts")
    xgboost_model_version: str = "xgboost-v1"
    use_real_dataset: bool = True
    real_dataset_path: Path = Path("app/data/international_results.csv")
    training_match_limit: int = 1000
    seed_demo_data: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
