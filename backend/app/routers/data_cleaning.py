import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.services.data_cleaning import copy_row_for_clean_upload, missing_value_summary, rows_without_required_missing_values
from app.supabase_client import get_supabase_client

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


def _record_run(client: Any, upload_id: str, action_type: str, before: int, after: int, details: dict[str, Any]) -> str:
    response = client.table("data_cleaning_runs").insert({
        "upload_id": upload_id,
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
def analyse_missing_values(upload_id: str) -> dict[str, Any]:
    try:
        client = get_supabase_client()
        upload, rows, _ = _load_upload_and_rows(client, upload_id)
        summary = missing_value_summary(rows, upload["dataset_type"])
        run_id = _record_run(client, upload_id, "analyse", len(rows), len(rows), summary)
        return {"status": "success", "cleaning_run_id": run_id, "upload": upload, **summary}
    except HTTPException:
        raise
    except Exception as error:
        logger.exception("Unable to analyse missing values")
        raise HTTPException(status_code=502, detail=f"Supabase could not analyse this dataset: {error}") from error


@router.post("/remove-missing", status_code=status.HTTP_201_CREATED)
def remove_missing_values(payload: CleaningRequest) -> dict[str, Any]:
    try:
        client = get_supabase_client()
        upload, rows, table_name = _load_upload_and_rows(client, payload.upload_id)
        summary = missing_value_summary(rows, upload["dataset_type"])
        retained_rows = rows_without_required_missing_values(rows, upload["dataset_type"])
        removed_count = len(rows) - len(retained_rows)
        cleaned_upload_id = payload.upload_id

        if removed_count:
            original_name = Path(upload["original_filename"])
            cleaned_name = f"{original_name.stem}_cleaned{original_name.suffix or '.csv'}"
            new_upload = client.table("dataset_uploads").insert({
                "dataset_type": upload["dataset_type"],
                "original_filename": cleaned_name,
                "file_format": upload["file_format"],
                "record_count": len(retained_rows),
                "processing_status": "cleaned",
            }).execute().data[0]
            cleaned_upload_id = new_upload["id"]
            if retained_rows:
                copied_rows = [copy_row_for_clean_upload(row, cleaned_upload_id) for row in retained_rows]
                client.table(table_name).insert(copied_rows).execute()

        details = {**summary, "cleaned_upload_id": cleaned_upload_id}
        run_id = _record_run(client, payload.upload_id, "remove_missing", len(rows), len(retained_rows), details)
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
        raise HTTPException(status_code=502, detail=f"Supabase could not clean this dataset: {error}") from error
