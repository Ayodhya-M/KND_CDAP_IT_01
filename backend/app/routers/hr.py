import logging
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from app.services.hr_upload import employee_rows_for_insert, validate_hr_csv
from app.supabase_client import get_supabase_client

router = APIRouter(prefix="/hr", tags=["HR dataset"])
logger = logging.getLogger(__name__)


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_hr_dataset(file: UploadFile = File(...)) -> JSONResponse:
    """Validate a pilot HR CSV and persist all valid rows as one dataset upload."""
    file_name = file.filename or "hr_dataset.csv"
    if Path(file_name).suffix.lower() != ".csv":
        raise HTTPException(status_code=400, detail="Only CSV files are supported for HR upload")

    validation = validate_hr_csv(await file.read(), file_name)
    if not validation.is_valid:
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=validation.summary)

    try:
        client = get_supabase_client()
        upload_response = client.table("dataset_uploads").insert({
            "dataset_type": "hr",
            "original_filename": file_name,
            "file_format": "csv",
            "record_count": validation.summary["total_records"],
            "processing_status": "uploaded",
        }).execute()
        upload_id = upload_response.data[0]["id"]
        client.table("employee_records").insert(employee_rows_for_insert(validation.dataframe, upload_id)).execute()
        client.table("validation_reports").insert({
            "upload_id": upload_id,
            "total_records": validation.summary["total_records"],
            "missing_value_count": sum(validation.summary["missing_values"].values()),
            "duplicate_record_count": 0,
            "invalid_date_count": 0,
            "validation_status": "passed",
            "report_data": validation.summary,
        }).execute()
    except Exception as error:
        logger.exception("Unable to store validated HR upload")
        raise HTTPException(
            status_code=502,
            detail=f"HR dataset validation passed, but Supabase could not store it: {error}",
        ) from error

    return JSONResponse(status_code=status.HTTP_201_CREATED, content={**validation.summary, "upload_id": upload_id})
