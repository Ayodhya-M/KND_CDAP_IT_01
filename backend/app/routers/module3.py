from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from app.services.module3_export import export_contract, pilot_export_csv, build_pilot_export, FEATURE_COLUMNS
from app.services.module3_prediction import get_model_status, load_evaluation_report, predict_saved_model
from app.services.eesi import VERSION as EESI_VERSION


router = APIRouter(prefix="/module3", tags=["Module 3 integration"])


class PredictionRequest(BaseModel):
    record: dict[str, Any]


@router.get('/pilot-records')
def pilot_prediction_records():
    status = get_model_status()
    formula = status.get('eesi_integration', {}).get('formula_id')
    if not status.get('model_available') or not formula:
        raise HTTPException(status_code=503, detail='Prepare the synthetic demo model with scripts/prepare_module3_demo.py first.')
    if (status.get('source_rows') != 300 or status.get('feature_columns') != FEATURE_COLUMNS or
            status['eesi_integration'].get('formula_version') != EESI_VERSION):
        raise HTTPException(status_code=503, detail='This saved model does not match the 300-person pilot and EESI contract. Use matching custom inputs or prepare the demo model.')
    rows = build_pilot_export(formula, employee_count=300)
    return {'dataset_kind': 'synthetic_pilot_only', 'formula_id': formula,
            'records': [{'employee_id': row['EmployeeID'], 'month': row['ObservationMonth'],
                         'record': {field: row[field] for field in FEATURE_COLUMNS}} for row in rows]}


@router.get("/integration-contract")
def get_integration_contract() -> dict[str, object]:
    """Describe the stable Module 1/2 to Module 3 PP1 pilot interface."""
    return export_contract()


@router.get("/pilot-export", response_class=PlainTextResponse)
def download_pilot_export(
    formula_id: str = Query(default="additive", description="Selected exploratory EESI formula"),
) -> PlainTextResponse:
    """Download a synthetic, ML-ready pilot CSV; not for research performance claims."""
    try:
        content = pilot_export_csv(formula_id)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    headers = {
        "Content-Disposition": f'attachment; filename="module3_synthetic_pilot_{formula_id}.csv"',
        "X-Dataset-Provenance": "synthetic-pilot-only-not-research-evidence",
        "X-EESI-Formula-Id": formula_id,
    }
    return PlainTextResponse(content=content, media_type="text/csv", headers=headers)


@router.get("/prediction-status")
def prediction_status() -> dict[str, Any]:
    """Return safe metadata about the locally available Module 3 model."""
    return get_model_status()


@router.post("/predict")
def predict_turnover(payload: PredictionRequest) -> dict[str, Any]:
    """Predict from a saved Module 3 artifact; does not provide recommendations."""
    try:
        return predict_saved_model(payload.record)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except (RuntimeError, FileNotFoundError) as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.get("/evaluation")
def evaluation_report() -> dict[str, Any]:
    """Return the saved held-out evaluation report for the local model artifact."""
    try:
        return load_evaluation_report()
    except (RuntimeError, FileNotFoundError) as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
