from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.module4.schemas.integration import (
    Module1EmployeeContext,
    Module2EESIResult,
    Module3PredictionResult,
)


def employee_data() -> dict[str, object]:
    return {
        "id": uuid4(),
        "upload_id": uuid4(),
        "employee_id": "EMP001",
        "age": None,
        "gender": None,
        "salary": None,
        "department": None,
        "job_role": None,
        "job_level": None,
        "business_travel": None,
        "distance_from_home": None,
        "education_field": None,
        "marital_status": None,
        "overtime": None,
        "job_satisfaction": None,
        "environment_satisfaction": None,
        "work_life_balance": None,
        "total_working_years": None,
        "years_at_company": None,
        "join_date": None,
        "resignation_date": None,
        "observation_date": None,
        "attrition": False,
        "raw_data": {},
        "created_at": datetime.now(timezone.utc),
    }


def test_module1_employee_accepts_nullable_database_fields() -> None:
    employee = Module1EmployeeContext.model_validate(employee_data())

    assert employee.employee_id == "EMP001"
    assert employee.salary is None
    assert employee.observation_date is None


def test_employee_identifier_cannot_be_blank() -> None:
    with pytest.raises(ValidationError):
        Module1EmployeeContext.model_validate({**employee_data(), "employee_id": "  "})


@pytest.mark.parametrize("probability", [-0.01, 1.01])
def test_module3_probability_must_be_between_zero_and_one(probability: float) -> None:
    with pytest.raises(ValidationError):
        Module3PredictionResult(
            employee_id="EMP001",
            turnover_probability=probability,
            risk_level="provisional-level",
        )


def test_module2_score_has_no_invented_range() -> None:
    result = Module2EESIResult(
        employee_id="EMP001",
        eesi_score=125.5,
        economic_pressure_level="module-2-defined-level",
    )

    assert result.eesi_score == 125.5


def test_module2_result_requires_a_link_identifier() -> None:
    with pytest.raises(ValidationError):
        Module2EESIResult(eesi_score=10, economic_pressure_level="unknown")
