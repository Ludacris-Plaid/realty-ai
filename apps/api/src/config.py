from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "RealtyAI"
    debug: bool = True
    database_url: str = "postgresql+asyncpg://realty:realty_local_dev@localhost:5433/realty_ai"
    redis_url: str = "redis://localhost:6379/0"
    llm_api_base: str = "http://localhost:8000/v1"
    llm_api_key: str = "not-needed"
    llm_default_model: str = "openai/gpt-4o-mini"
    cors_origins: str = "http://localhost:3000"
    auth_secret_key: str = "change-me-in-production"
    auth_algorithm: str = "HS256"
    auth_token_expire_minutes: int = 1440

    model_config = {"env_file": ".env", "env_prefix": "", "extra": "ignore"}


settings = Settings()
