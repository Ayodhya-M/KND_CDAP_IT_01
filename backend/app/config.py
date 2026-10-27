from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    app_name: str = "KND CDAP API"
    api_v1_prefix: str = "/api/v1"
    # Placeholder values let the health endpoint run before local setup.
    # Replace both values in backend/.env before using Supabase features.
    supabase_url: str = "https://your-project-ref.supabase.co"
    supabase_service_role_key: str = "your_supabase_service_role_key"
    cors_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
