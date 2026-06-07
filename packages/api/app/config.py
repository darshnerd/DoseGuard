from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_prefix="DOSEGUARD_")

    app_name: str = "dosegaurd-api"
    environment: str = "development"
    log_level: str = "INFO"
    
    rxnav_base: str = "https://rxnav.nlm.nih.gov/REST"
    rxnav_timeout: float = 5.0
    
    database_url: str = "sqlite:///./doseguard.db"


@lru_cache
def get_settings():
    return Settings()
