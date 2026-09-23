from functools import lru_cache
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_env: str = "development"
    debug: bool = True
    secret_key: str = "dev-only-change-me"
    database_url: str = "sqlite+aiosqlite:///./hospira.db"
    groq_api_key: str | None = None
    groq_model: str = "llama-3.1-8b-instant"
    cors_origins: str = "http://localhost:5173"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_list(self) -> list[str]:
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @model_validator(mode="after")
    def validate_production(self):
        if self.is_production and not self.database_url.startswith(("postgresql", "postgres")):
            raise ValueError("Production requires DATABASE_URL to point to PostgreSQL")
        return self

@lru_cache
def get_settings() -> Settings:
    return Settings()

def reset_settings_cache():
    get_settings.cache_clear()
