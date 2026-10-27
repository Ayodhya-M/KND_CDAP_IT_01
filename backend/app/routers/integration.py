import logging
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.services.data_integration import build_integrated_records
from app.supabase_client import get_supabase_client

router = APIRouter(prefix="/integration", tags=["Data integration"])
logger = logging.getLogger(__name__)


class IntegrationRequest(BaseModel):
    temporal_mapping_run_id: str


@router.get("/mapping-runs")
def available_mapping_runs() -> dict[str, list[dict[str, Any]]]:
    try:
        response = get_supabase_client().table("temporal_mapping_runs").select(
            "id,hr_upload_id,economic_upload_id,total_employee_records,mapped_record_count,unmapped_record_count,mapping_accuracy,status,created_at"
        ).order("created_at", desc=True).execute()
        return {"mapping_runs": response.data}
    except Exception as error:
        logger.exception("Unable to list temporal mapping runs")
        raise HTTPException(status_code=502, detail=f"Supabase could not load mapping runs: {error}") from error


@router.post("/generate", status_code=status.HTTP_201_CREATED)
def generate_integrated_dataset(payload: IntegrationRequest) -> dict[str, Any]:
    try:
        client = get_supabase_client()
        mapping_run_response = client.table("temporal_mapping_runs").select("*").eq(
            "id", payload.temporal_mapping_run_id
        ).execute()
        if not mapping_run_response.data:
            raise HTTPException(status_code=404, detail="Selected temporal mapping run was not found")
        mapping_run = mapping_run_response.data[0]
        mappings = client.table("temporal_mappings").select("*").eq(
            "mapping_run_id", payload.temporal_mapping_run_id
        ).execute().data
        if not mappings:
            raise HTTPException(status_code=400, detail="Selected temporal mapping run has no mapping records")

        employee_ids = list({mapping["employee_record_id"] for mapping in mappings})
        indicator_ids = list({mapping["economic_indicator_id"] for mapping in mappings if mapping.get("economic_indicator_id")})
        employees = client.table("employee_records").select("*").in_("id", employee_ids).execute().data
        indicators = client.table("economic_indicators").select("*").in_("id", indicator_ids).execute().data if indicator_ids else []

        run_response = client.table("integration_runs").insert({
            "hr_upload_id": mapping_run["hr_upload_id"],
            "economic_upload_id": mapping_run["economic_upload_id"],
            "temporal_mapping_run_id": mapping_run["id"],
            "total_hr_records": len(employees),
            "status": "processing",
        }).execute()
        integration_run_id = run_response.data[0]["id"]
        records, preview, skipped = build_integrated_records(mappings, employees, indicators, integration_run_id)
        if records:
            client.table("integrated_records").insert(records).execute()
        mapping_rate = round((len(records) / len(employees)) * 100, 2) if employees else 0
        client.table("integration_runs").update({
            "mapped_record_count": len(records), "mapping_accuracy": mapping_rate,
            "status": "successful",
        }).eq("id", integration_run_id).execute()
    except HTTPException:
        raise
    except Exception as error:
        logger.exception("Unable to generate integrated dataset")
        raise HTTPException(status_code=502, detail=f"Supabase could not generate the integrated dataset: {error}") from error

    return {
        "status": "success", "integration_run_id": integration_run_id,
        "source_mapping_run_id": payload.temporal_mapping_run_id,
        "total_hr_records": len(employees), "integrated_records": len(records),
        "unmatched_records": skipped, "integration_rate": mapping_rate,
        "records": preview,
    }
