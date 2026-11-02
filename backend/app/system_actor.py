"""Validation for the explicitly configured research-prototype audit actor."""

from uuid import UUID

from fastapi import HTTPException, status

from app.config import get_settings
from app.supabase_client import get_supabase_client


def require_research_system_actor() -> UUID:
    """Return a configured, existing profile ID without choosing one implicitly."""
    actor_id = get_settings().research_system_actor_id
    if actor_id is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Audited prototype operations are disabled until RESEARCH_SYSTEM_ACTOR_ID "
                "is configured on the backend"
            ),
        )
    try:
        profiles = (
            get_supabase_client()
            .table("profiles")
            .select("id,role")
            .eq("id", str(actor_id))
            .limit(1)
            .execute()
            .data
        )
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The configured research system actor could not be verified",
        ) from error
    if not profiles:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The configured research system actor does not reference an existing project profile",
        )
    if profiles[0].get("role") not in {"researcher", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The configured research system actor is not authorized for this operation",
        )
    return actor_id
