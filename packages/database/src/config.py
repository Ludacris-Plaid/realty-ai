from pydantic_settings import BaseSettings


class DBSettings(BaseSettings):
    database_url: str = "postgresql+asyncpg://realty:realty_local_dev@localhost:5433/realty_ai"
    debug: bool = False

    model_config = {"env_prefix": ""}


settings = DBSettings()
