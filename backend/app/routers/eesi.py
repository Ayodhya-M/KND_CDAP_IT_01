from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.eesi import calculate, metadata, pilot_preview
from app.services.eesi_real import REAL_BOUNDS, REAL_VERSION, load_real_summary
from typing import Literal
import sqlite3
from app.services.hies_data import get_dataset, import_prepared, calculate_scenario
from app.services.eesi_formula_d import FormulaDConfig, FormulaDInputs, calculate_formula_d, compare_dataset
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/eesi", tags=["EESI proof of concept"])


@router.post('/formula-d/scenario')
def formula_d_scenario(payload: FormulaDInputs):
    try:
        return calculate_formula_d(**payload.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.post('/hies/formula-d')
def formula_d_comparison(payload: FormulaDConfig):
    try:
        return compare_dataset(get_dataset(), payload)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except (OSError, sqlite3.Error) as error:
        raise HTTPException(status_code=503, detail='The local HIES dataset could not be read.') from error


@router.post('/hies/formula-d/export')
def formula_d_export(payload: FormulaDConfig):
    return JSONResponse(formula_d_comparison(payload), headers={
        'Content-Disposition': 'attachment; filename="hies2019-formula-d.json"'})


@router.get('/hies')
def hies_dataset():
    try:
        return get_dataset()
    except (OSError, ValueError, sqlite3.Error) as error:
        raise HTTPException(status_code=503, detail='The local HIES dataset could not be read.') from error


@router.post('/hies/import-prepared')
def import_hies_dataset():
    try:
        return import_prepared()
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail='Prepare the HIES sample with scripts/clean_hies2019_eesi.py first.') from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except (OSError, sqlite3.Error) as error:
        raise HTTPException(status_code=503, detail='The private HIES dataset could not be stored.') from error


class ScenarioRequest(BaseModel):
    salary: float = Field(gt=0, allow_inf_nan=False)
    inflation: float = Field(allow_inf_nan=False)
    cpi: float = Field(gt=0, allow_inf_nan=False)
    unemployment: float = Field(ge=0, le=100, allow_inf_nan=False)
    reference_salary: float = Field(default=50000, gt=0, allow_inf_nan=False)
    reference_profile: Literal["pilot", "lfs2024"] = "pilot"


class HiesScenarioRequest(BaseModel):
    salary: float = Field(gt=0, allow_inf_nan=False)
    inflation: float = Field(allow_inf_nan=False)
    cpi: float = Field(gt=0, allow_inf_nan=False)
    unemployment: float = Field(ge=0, le=100, allow_inf_nan=False)
    reference_salary: float = Field(default=50000, gt=0, allow_inf_nan=False)


@router.post('/hies/scenario')
def hies_scenario(payload: HiesScenarioRequest):
    return calculate_scenario(**payload.model_dump())


@router.get("/metadata")
def get_metadata():
    return metadata()


@router.get("/pilot")
def get_pilot():
    try:
        return pilot_preview()
    except (OSError, ValueError) as error:
        raise HTTPException(status_code=503, detail="EESI pilot data is unavailable") from error


@router.post("/scenario")
def scenario(payload: ScenarioRequest):
    values = payload.model_dump(exclude={"reference_profile"})
    if payload.reference_profile == "lfs2024":
        return calculate(**values, bounds=REAL_BOUNDS, version=REAL_VERSION)
    return calculate(**values)


@router.get("/real-data")
def get_real_data():
    try:
        return load_real_summary()
    except (OSError, ValueError) as error:
        raise HTTPException(status_code=503, detail="Prepare the LFS 2024 aggregate using scripts/prepare_lfs2024.py") from error
