import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.services.data_cleaning import missing_value_summary, rows_without_required_missing_values
from app.supabase_client import get_supabase_client
from app.system_actor import require_research_system_actor

router = APIRouter(prefix="/data-cleaning", tags=["Data cleaning"])
logger = logging.getLogger(__name__)


class CleaningRequest(BaseModel):
    upload_id: str


def _load_upload_and_rows(client: Any, upload_id: str) -> tuple[dict[str, Any], list[dict[str, Any]], str]:
    upload_response = client.table("dataset_uploads").select("*").eq("id", upload_id).execute()
    if not upload_response.data:
        raise HTTPException(status_code=404, detail="Selected upload was not found")
    upload = upload_response.data[0]
    dataset_type = upload["dataset_type"]
    table_name = "employee_records" if dataset_type == "hr" else "economic_indicators"
    rows = client.table(table_name).select("*").eq("upload_id", upload_id).execute().data
    return upload, rows, table_name


def _record_run(
    client: Any, upload_id: str, initiated_by: str, action_type: str,
    before: int, after: int, details: dict[str, Any],
) -> str:
    response = client.table("data_cleaning_runs").insert({
        "upload_id": upload_id,
        "initiated_by": initiated_by,
        "action_type": action_type,
        "rows_before": before,
        "rows_after": after,
        "affected_row_count": before - after,
        "status": "completed",
        "details": details,
    }).execute()
    return response.data[0]["id"]


@router.get("/uploads")
def available_uploads() -> dict[str, list[dict[str, Any]]]:
    try:
        response = get_supabase_client().table("dataset_uploads").select(
            "id,dataset_type,original_filename,record_count,uploaded_at"
        ).execute()
        return {"uploads": response.data}
    except Exception as error:
        logger.exception("Unable to list data-cleaning uploads")
        raise HTTPException(status_code=502, detail=f"Supabase could not load uploads: {error}") from error


@router.get("/analyse/{upload_id}")
def analyse_missing_values(
    upload_id: str,
    actor_id: UUID = Depends(require_research_system_actor),
) -> dict[str, Any]:
    try:
        client = get_supabase_client()
        upload, rows, _ = _load_upload_and_rows(client, upload_id)
        summary = missing_value_summary(rows, upload["dataset_type"])
        run_id = _record_run(client, upload_id, str(actor_id), "analyse", len(rows), len(rows), summary)
        return {"status": "success", "cleaning_run_id": run_id, "upload": upload, **summary}
    except HTTPException:
        raise
    except Exception as error:
        logger.exception("Unable to analyse missing values")
        raise _cleaning_database_error(error, "analyse") from error


@router.post("/remove-missing", status_code=status.HTTP_201_CREATED)
def remove_missing_values(
    payload: CleaningRequest,
    actor_id: UUID = Depends(require_research_system_actor),
) -> dict[str, Any]:
    try:
        client = get_supabase_client()
        upload, rows, _ = _load_upload_and_rows(client, payload.upload_id)
        summary = missing_value_summary(rows, upload["dataset_type"])
        retained_rows = rows_without_required_missing_values(rows, upload["dataset_type"])
        removed_count = len(rows) - len(retained_rows)
        if removed_count:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "Removing rows is disabled until the multi-table cleaning operation is available "
                    "as one transactional database function; no records were changed"
                ),
            )

        cleaned_upload_id = payload.upload_id
        details = {**summary, "cleaned_upload_id": cleaned_upload_id}
        run_id = _record_run(
            client, payload.upload_id, str(actor_id), "remove_missing",
            len(rows), len(retained_rows), details,
        )
        return {
            "status": "success", "cleaning_run_id": run_id,
            "source_upload_id": payload.upload_id, "cleaned_upload_id": cleaned_upload_id,
            "rows_before": len(rows), "rows_after": len(retained_rows),
            "removed_records": removed_count, "missing_values": summary["missing_values"],
            "message": "No rows contained missing required values; the original upload remains the cleaned dataset." if not removed_count else "A cleaned dataset was created without rows containing missing required values.",
        }
    except HTTPException:
        raise
    except Exception as error:
        logger.exception("Unable to remove missing values")
        raise _cleaning_database_error(error, "clean") from error


def _cleaning_database_error(error: Exception, operation: str) -> HTTPException:
    """Translate database integrity errors without leaking server details."""
    code = getattr(error, "code", None)
    if code in {"23502", "23503", "23505", "23514"}:
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"The database rejected the {operation} audit record because an integrity constraint was not satisfied",
        )
    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=f"The data store could not complete the {operation} operation",
    )
