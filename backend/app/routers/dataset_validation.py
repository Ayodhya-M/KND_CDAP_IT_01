import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from app.services.dataset_validation import validate_integrated_dataset
from app.supabase_client import get_supabase_client

router = APIRouter(prefix="/dataset-validation", tags=["Dataset validation"])
logger = logging.getLogger(__name__)


@router.get("/integration-runs")
def available_integration_runs() -> dict[str, list[dict[str, Any]]]:
    try:
        response = get_supabase_client().table("integration_runs").select(
            "id,total_hr_records,mapped_record_count,mapping_accuracy,status,created_at"
        ).eq("status", "successful").order("created_at", desc=True).execute()
        return {"integration_runs": response.data}
    except Exception as error:
        logger.exception("Unable to list integration runs for validation")
        raise HTTPException(status_code=502, detail=f"Supabase could not load integrated datasets: {error}") from error


@router.get("/integration/{integration_run_id}")
def validate_integration_run(integration_run_id: str) -> dict[str, Any]:
    try:
        client = get_supabase_client()
        run_response = client.table("integration_runs").select("*").eq("id", integration_run_id).execute()
        if not run_response.data:
            raise HTTPException(status_code=404, detail="Selected integration run was not found")
        integration_run = run_response.data[0]
        mapping_run_id = integration_run.get("temporal_mapping_run_id")
        if not mapping_run_id:
            raise HTTPException(status_code=400, detail="Selected integration run has no temporal mapping reference")
        hr_records = client.table("employee_records").select("id").eq("upload_id", integration_run["hr_upload_id"]).execute().data
        economic_indicators = client.table("economic_indicators").select("indicator_month").eq("upload_id", integration_run["economic_upload_id"]).execute().data
        temporal_mappings = client.table("temporal_mappings").select("employee_record_id,mapping_status").eq("mapping_run_id", mapping_run_id).execute().data
        integrated_records = client.table("integrated_records").select("*").eq("integration_run_id", integration_run_id).execute().data
        report = validate_integrated_dataset(hr_records, economic_indicators, temporal_mappings, integrated_records)
    except HTTPException:
        raise
    except Exception as error:
        logger.exception("Unable to validate integrated dataset")
        raise HTTPException(status_code=502, detail=f"Supabase could not validate this integrated dataset: {error}") from error

    return {"status": "success", "integration_run_id": integration_run_id, **report}
