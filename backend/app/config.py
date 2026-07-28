"""Application config via pydantic-settings."""
from __future__ import annotations

import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://realty:realty_dev@postgres:5432/realtyai"

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # Auth
    auth_secret_key: str = "realty-ai-v1-dev-secret-key-change-in-prod"
    auth_algorithm: str = "HS256"
    auth_token_expire_minutes: int = 1440  # 24h

    # LLM
    deepseek_api_key: Optional[str] = None
    deepseek_model: str = "deepseek-v4-flash"
    deepseek_base_url: str = "https://api.deepseek.com/v1"

    # Embeddings
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_dim: int = 384

    # Celery
    celery_broker_url: str = "redis://redis:6379/1"
    celery_result_backend: str = "redis://redis:6379/2"

    # CORS
    cors_origins: str = "http://localhost:3000"

    # Logging
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

# Override from env vars for production
for key in ("database_url", "auth_secret_key", "deepseek_api_key"):
    env_val = os.environ.get(key.upper())
    if env_val:
        setattr(settings, key, env_val)
