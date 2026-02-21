from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List
import os


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    AIMA_ENV: str = "development"
    AIMA_SECRET_KEY: str = "change-this-secret"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    DATABASE_URL: str = "postgresql+asyncpg://aima:aima_password@localhost:5432/aima"
    DATABASE_URL_SYNC: str = "postgresql://aima:aima_password@localhost:5432/aima"

    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC_EVENTS: str = "aima.events"
    KAFKA_TOPIC_ALERTS: str = "aima.alerts"

    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET_RAW: str = "aima-raw"
    MINIO_BUCKET_PROCESSED: str = "aima-processed"
    MINIO_BUCKET_MODELS: str = "aima-models"
    MINIO_SECURE: bool = False

    MLFLOW_TRACKING_URI: str = "http://localhost:5000"
    MLFLOW_EXPERIMENT_NAME: str = "aima-experiments"

    OPENAI_API_KEY: str = ""
    HUGGINGFACE_TOKEN: str = ""

    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    API_PREFIX: str = "/api/v1"
    API_WORKERS: int = 4
    API_PORT: int = 8000

    SHOPIFY_API_KEY: str = ""
    SHOPIFY_API_SECRET: str = ""
    HUBSPOT_API_KEY: str = ""
    KLAVIYO_API_KEY: str = ""
    META_ADS_APP_ID: str = ""
    META_ADS_APP_SECRET: str = ""
    META_ADS_ACCESS_TOKEN: str = ""
    GOOGLE_ADS_CLIENT_ID: str = ""
    GOOGLE_ADS_CLIENT_SECRET: str = ""
    TWITTER_BEARER_TOKEN: str = ""

    @property
    def is_production(self) -> bool:
        return self.AIMA_ENV == "production"

    @property
    def is_development(self) -> bool:
        return self.AIMA_ENV == "development"


settings = Settings()
