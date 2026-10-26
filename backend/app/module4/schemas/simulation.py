"""Contracts for the non-persistent, illustrative Module 4 scenario prototype."""

from pydantic import Field, model_validator

from app.module4.schemas.decision_support import DevelopmentMetadata, PrioritizedRecommendation
from app.module4.schemas.integration import IntegrationModel


SIMULATION_LABEL = "Illustrative What-if Prototype — Not a Validated Turnover Forecast"


class WhatIfChanges(IntegrationModel):
    salary: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    overtime: bool | None = None
    job_satisfaction: int | None = Field(default=None, ge=1, le=4)
    work_life_balance: int | None = Field(default=None, ge=1, le=4)

    @model_validator(mode="after")
    def require_a_change(self) -> "WhatIfChanges":
        if all(value is None for value in self.model_dump().values()):
            raise ValueError("At least one supported scenario value is required")
        return self


class ScenarioValues(IntegrationModel):
    salary: float | None = None
    overtime: bool | None = None
    job_satisfaction: int | None = None
    work_life_balance: int | None = None


class WhatIfSimulationResponse(IntegrationModel):
    employee_id: str
    label: str = SIMULATION_LABEL
    original_values: ScenarioValues
    simulated_values: ScenarioValues
    original_turnover_probability: float = Field(ge=0, le=1)
    simulated_turnover_probability: float = Field(ge=0, le=1)
    probability_difference: float
    original_recommendations: list[PrioritizedRecommendation]
    simulated_recommendations: list[PrioritizedRecommendation]
    removed_risk_factors: list[str]
    retained_risk_factors: list[str]
    assumptions: list[str]
    disclaimer: str
    metadata: DevelopmentMetadata
