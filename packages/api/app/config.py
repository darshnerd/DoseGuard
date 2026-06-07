from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_prefix="DOSEGUARD_")

    app_name: str = "dosegaurd-api"
    environment: str = "development"
    log_level: str = "INFO"


@lru_cache
def get_settings():
    return Settings()
