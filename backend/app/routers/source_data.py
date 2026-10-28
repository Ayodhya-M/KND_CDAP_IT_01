"""Minimal source-aware additions to Module 1 without mixing incompatible cohorts."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.services import source_datasets

router = APIRouter(prefix='/source-data', tags=['Module 1 additional sources'])


class Scenario(BaseModel):
    salary: float | None = Field(default=None, gt=0, allow_inf_nan=False)


@router.get('')
def sources():
    return {'datasets': source_datasets.list_datasets(), 'storage': 'private_local',
            'note': 'Additional source datasets are separate from Supabase HR uploads and HIES.'}


@router.get('/{dataset_id}/records')
def records(dataset_id: str):
    try:
        return {'records': source_datasets.record_choices(dataset_id)}
    except KeyError as error:
        raise HTTPException(status_code=404, detail='Source dataset not found') from error


@router.post('/{dataset_id}/records/{record_id}/analyse')
def analyse(dataset_id: str, record_id: str, scenario: Scenario):
    try:
        return source_datasets.analyse(dataset_id, record_id, salary=scenario.salary)
    except KeyError as error:
        raise HTTPException(status_code=404, detail='Source dataset or record not found') from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except (RuntimeError, FileNotFoundError) as error:
        raise HTTPException(status_code=503, detail='The source-specific model is unavailable. Re-run the authorized source importer.') from error
