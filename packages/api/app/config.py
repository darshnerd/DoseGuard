from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_prefix="DOSEGUARD_")

    app_name: str = "dosegaurd-api"
    environment: str = "development"
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:5173"]
    
    rxnav_base: str = "https://rxnav.nlm.nih.gov/REST"
    rxnav_timeout: float = 5.0
    
    database_url: str = "sqlite:///./doseguard.db"
    secret_key: str = "dev-only-insecure-key-change-me-please-0123456789abcd"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15
    refresh_token_days: int = 7
    max_upload_mb: int = 5

    pubchem_live: bool = True

    @model_validator(mode="after")
    def _require_secret_in_prod(self):
        if self.environment == "production":
            if self.secret_key.startswith("dev-only") or len(self.secret_key) < 32:
                raise ValueError(
                    "DOSEGUARD_SECRET_KEY must be a strong (>=32 char) value in production"
                )
        return self


@lru_cache
def get_settings():
    return Settings()
