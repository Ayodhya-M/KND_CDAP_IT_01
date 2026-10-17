from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    app_name: str = "KND CDAP API"
    api_v1_prefix: str = "/api/v1"
    # Placeholder values let the health endpoint run before local setup.
    # Replace both values in backend/.env before using Supabase features.
    supabase_url: str = "https://your-project-ref.supabase.co"
    supabase_service_role_key: str = "your_supabase_service_role_key"
    backend_port: int = 8000
    cors_origins: str = "http://localhost:5173"
    module2_provider: Literal["mock", "real"] = "mock"
    module3_provider: Literal["mock", "real"] = "mock"
    # Research selections intentionally have no defaults. Real providers fail
    # clearly until the responsible module owners approve these contracts.
    module2_eesi_formula: str | None = None
    module2_reference_profile: Literal["pilot", "lfs2024"] = "pilot"
    module3_positive_class_label: str | None = None

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
