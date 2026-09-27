"""Contracts at the boundary between Modules 1, 2, 3, and 4.

The Module 1 models mirror fields verified in the current Supabase schema.
The Module 2 and Module 3 models are deliberately small, provisional contracts;
they do not calculate EESI or turnover risk.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class IntegrationModel(BaseModel):
    """Common strict configuration for records crossing module boundaries."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Module1EmployeeContext(IntegrationModel):
    """Employee fields currently stored by Module 1.

    ``id`` is the internal Supabase row UUID. ``employee_id`` is the external
    HR identifier; callers must not use one as a substitute for the other.
    """

    id: UUID
    upload_id: UUID
    employee_id: str = Field(min_length=1)
    age: int | None = Field(default=None, ge=14, le=100)
    gender: Literal["Female", "Male", "Other"] | None = None
    salary: Decimal | None = Field(default=None, ge=0)
    department: str | None = None
    job_role: str | None = None
    job_level: int | None = Field(default=None, ge=1, le=5)
    business_travel: Literal["Non-Travel", "Travel_Rarely", "Travel_Frequently"] | None = None
    distance_from_home: int | None = Field(default=None, ge=0)
    education_field: str | None = None
    marital_status: str | None = None
    overtime: bool | None = None
    job_satisfaction: int | None = Field(default=None, ge=1, le=4)
    environment_satisfaction: int | None = Field(default=None, ge=1, le=4)
    work_life_balance: int | None = Field(default=None, ge=1, le=4)
    total_working_years: int | None = Field(default=None, ge=0)
    years_at_company: int | None = Field(default=None, ge=0)
    join_date: date | None = None
    resignation_date: date | None = None
    observation_date: date | None = None
    attrition: bool
    raw_data: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class Module1EconomicContext(IntegrationModel):
    """Economic indicator row linked to an employee by Module 1 mapping."""

    id: UUID
    upload_id: UUID
    indicator_month: date
    inflation_rate: Decimal | None = None
    unemployment_rate: Decimal | None = None
    cost_of_living_index: Decimal | None = None
    cpi_index: Decimal | None = None
    policy_interest_rate_percent: Decimal | None = None
    usd_lkr_exchange_rate: Decimal | None = None
    gdp_growth_rate_percent: Decimal | None = None


class Module2EESIResult(IntegrationModel):
    """PROVISIONAL Module 2 boundary; align it with Module 2's real contract.

    No score range or pressure-level enum is imposed because Module 2 has not
    yet supplied those definitions. This model performs no EESI calculation.
    """

    employee_id: str | None = Field(default=None, min_length=1)
    mapping_id: UUID | None = None
    eesi_score: float = Field(allow_inf_nan=False)
    economic_pressure_level: str = Field(min_length=1)

    @model_validator(mode="after")
    def require_link_identifier(self) -> "Module2EESIResult":
        if self.employee_id is None and self.mapping_id is None:
            raise ValueError("employee_id or mapping_id is required")
        return self


class Module3RiskFactor(IntegrationModel):
    """PROVISIONAL generic explanation item from Module 3.

    ``contribution`` is not assumed to be a SHAP value. Module 3 must later
    define its meaning, direction, scale, and feature naming convention.
    """

    feature_name: str = Field(min_length=1)
    feature_value: Any = None
    contribution: float = Field(allow_inf_nan=False)


class Module3PredictionResult(IntegrationModel):
    """PROVISIONAL Module 3 prediction boundary; replace/alignment is pending."""

    employee_id: str = Field(min_length=1)
    turnover_probability: float = Field(ge=0, le=1, allow_inf_nan=False)
    risk_level: str = Field(min_length=1)
    risk_factors: list[Module3RiskFactor] = Field(default_factory=list)


class Module4AnalysisInput(IntegrationModel):
    """Validated combined input for a future Module 4 risk analyzer."""

    employee: Module1EmployeeContext
    economic_context: Module1EconomicContext | None = None
    eesi_result: Module2EESIResult
    prediction_result: Module3PredictionResult

    @model_validator(mode="after")
    def identifiers_must_match(self) -> "Module4AnalysisInput":
        expected = self.employee.employee_id
        if self.eesi_result.employee_id is not None and self.eesi_result.employee_id != expected:
            raise ValueError("Module 2 employee_id does not match Module 1 employee_id")
        if self.prediction_result.employee_id != expected:
            raise ValueError("Module 3 employee_id does not match Module 1 employee_id")
        return self
