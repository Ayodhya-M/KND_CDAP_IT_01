from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers.auth import router as auth_router
from app.supabase_client import get_supabase_client

settings = get_settings()

app = FastAPI(title=settings.app_name, version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router, prefix=settings.api_v1_prefix)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Lightweight endpoint for checking that the API is running."""
    return {"status": "ok", "service": settings.app_name}


@app.get(f"{settings.api_v1_prefix}/status", tags=["status"])
def api_status() -> dict[str, str]:
    return {"message": "KND CDAP API is ready"}


@app.get(f"{settings.api_v1_prefix}/supabase/status", tags=["status"])
def supabase_status() -> dict[str, str]:
    """Confirm that server-side Supabase credentials can access the project."""
    try:
        # This is a supported server-side call. It verifies both the project URL
        # and the service-role key without creating or changing any user data.
        get_supabase_client().auth.admin.list_users(page=1, per_page=1)
    except Exception as error:
        raise HTTPException(status_code=503, detail="Supabase connection unavailable") from error

    return {"status": "connected", "service": "supabase"}
