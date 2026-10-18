from supabase import Client, create_client

from app.config import get_settings


def get_supabase_client() -> Client:
    """Create a Supabase client using server-side credentials only."""
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_service_role_key)
