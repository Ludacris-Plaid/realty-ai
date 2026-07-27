from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "RealtyAI"
    debug: bool = True
    database_url: str = "postgresql+asyncpg://realty:realty_local_dev@localhost:5433/realty_ai"
    redis_url: str = "redis://localhost:6379/0"
    llm_api_base: str = "https://api.featherless.ai/v1"
    llm_api_key: str = "rc_39469c71f02a6f4d905bace1fff05adee3228beca9a0ddb85898ea20438d8435"
    llm_default_model: str = "unsloth/Qwen2.5-7B-Instruct"
    cors_origins: str = "http://localhost:3000"
    auth_secret_key: str = Field(default="change-me-in-production", validation_alias="AUTH_SECRET_KEY")

    @property
    def auth_secret(self) -> str:
        """Get auth secret from env or config file."""
        import os
        return os.environ.get("AUTH_SECRET_KEY", self.auth_secret_key)
    auth_algorithm: str = "HS256"
    auth_token_expire_minutes: int = 1440

    model_config = {"env_file": ".env", "env_prefix": "", "extra": "ignore"}


settings = Settings()
