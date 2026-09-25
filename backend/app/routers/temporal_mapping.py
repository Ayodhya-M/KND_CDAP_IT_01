import logging
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.services.temporal_mapping import build_monthly_mappings
from app.supabase_client import get_supabase_client

router = APIRouter(prefix="/temporal-mapping", tags=["Temporal mapping"])
logger = logging.getLogger(__name__)


class MappingRequest(BaseModel):
    hr_upload_id: str
    economic_upload_id: str


def _one_upload(client: Any, upload_id: str, expected_type: str) -> dict[str, Any]:
    response = client.table("dataset_uploads").select("id,dataset_type,original_filename,record_count,uploaded_at").eq("id", upload_id).execute()
    if not response.data or response.data[0]["dataset_type"] != expected_type:
        raise HTTPException(status_code=404, detail=f"Selected {expected_type} upload was not found")
    return response.data[0]


@router.get("/uploads")
def available_uploads() -> dict[str, list[dict[str, Any]]]:
    """List HR and macroeconomic uploads so one pair can be selected explicitly."""
    try:
        client = get_supabase_client()
        hr = client.table("dataset_uploads").select("id,original_filename,record_count,uploaded_at").eq("dataset_type", "hr").execute().data
        economic = client.table("dataset_uploads").select("id,original_filename,record_count,uploaded_at").eq("dataset_type", "economic").execute().data
        return {"hr_uploads": hr, "economic_uploads": economic}
    except Exception as error:
        logger.exception("Unable to list uploads for temporal mapping")
        raise HTTPException(status_code=502, detail=f"Supabase could not load upload choices: {error}") from error


@router.post("/preview", status_code=status.HTTP_201_CREATED)
def create_mapping_preview(payload: MappingRequest) -> dict[str, Any]:
    """Persist a month-based mapping preview for one selected upload pair."""
    if payload.hr_upload_id == payload.economic_upload_id:
        raise HTTPException(status_code=400, detail="HR and economic upload IDs must be different")
    try:
        client = get_supabase_client()
        _one_upload(client, payload.hr_upload_id, "hr")
        _one_upload(client, payload.economic_upload_id, "economic")
        employees = client.table("employee_records").select("id,employee_id,observation_date").eq("upload_id", payload.hr_upload_id).execute().data
        indicators = client.table("economic_indicators").select("id,indicator_month").eq("upload_id", payload.economic_upload_id).execute().data
        if not employees:
            raise HTTPException(status_code=400, detail="Selected HR upload has no employee records")
        if not indicators:
            raise HTTPException(status_code=400, detail="Selected economic upload has no monthly indicators")

        run_response = client.table("temporal_mapping_runs").insert({
            "hr_upload_id": payload.hr_upload_id,
            "economic_upload_id": payload.economic_upload_id,
            "employee_date_field": "observation_date",
            "status": "preview",
        }).execute()
        mapping_run_id = run_response.data[0]["id"]
        mapping_rows, preview_rows, summary = build_monthly_mappings(employees, indicators, mapping_run_id)
        client.table("temporal_mappings").insert(mapping_rows).execute()
        client.table("temporal_mapping_runs").update({
            "total_employee_records": summary["total_employee_records"],
            "mapped_record_count": summary["matched_records"],
            "unmapped_record_count": summary["unmatched_records"],
            "mapping_accuracy": summary["mapping_rate"],
        }).eq("id", mapping_run_id).execute()
    except HTTPException:
        raise
    except Exception as error:
        logger.exception("Unable to create temporal mapping preview")
        raise HTTPException(status_code=502, detail=f"Supabase could not create the temporal mapping preview: {error}") from error

    return {"status": "success", "mapping_run_id": mapping_run_id, **summary, "mappings": preview_rows}
