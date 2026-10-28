"""Validated outputs produced by the Module 4 proof-of-concept services."""

from typing import Any

from pydantic import Field

from app.module4.schemas.integration import IntegrationModel, Module3RiskFactor


class EmployeeProfileSummary(IntegrationModel):
    """Non-sensitive Module 1 fields useful to an HR reviewer."""

    department: str | None = None
    job_role: str | None = None
    job_level: int | None = None
    salary: float | None = None
    overtime: bool | None = None
    job_satisfaction: int | None = None
    work_life_balance: int | None = None
    years_at_company: int | None = None


class RiskAnalysis(IntegrationModel):
    employee_id: str = Field(min_length=1)
    turnover_probability: float = Field(ge=0, le=1)
    risk_level: str = Field(min_length=1)
    eesi_score: float
    economic_pressure_level: str = Field(min_length=1)
    important_factors: list[Module3RiskFactor]


class RecommendationCandidate(IntegrationModel):
    recommendation_id: str = Field(min_length=1)
    recommendation_type: str = Field(min_length=1)
    title: str = Field(min_length=1)
    category: str = Field(min_length=1)
    related_factor: str = Field(min_length=1)
    factor_value: Any = None
    factor_contribution: float
    intervention_relevance: float = Field(ge=0, le=1)
    suggested_action: str = Field(min_length=1)
    rule_version: str = Field(default="module4-prototype-rules-v2", min_length=1)
    eligibility_basis: str = Field(
        default="Positive supported factor supplied by Module 3.", min_length=1,
    )


class PriorityValues(IntegrationModel):
    turnover_risk: float = Field(ge=0, le=1)
    factor_contribution: float = Field(ge=0, le=1)
    economic_pressure: float = Field(ge=0, le=1)
    intervention_relevance: float = Field(ge=0, le=1)


class PriorityBreakdown(IntegrationModel):
    formula: str
    inputs: PriorityValues
    weights: PriorityValues
    weighted_components: PriorityValues
    raw_weighted_total: float = Field(ge=0, le=1)
    score: float = Field(ge=0, le=100)


class PrioritySensitivityResult(IntegrationModel):
    scenario_id: str
    label: str
    weights: PriorityValues
    score: float = Field(ge=0, le=100)
    priority_level: str
    rank: int = Field(ge=1)


class PrioritizedRecommendation(IntegrationModel):
    recommendation_id: str
    recommendation_type: str
    title: str
    category: str
    related_factor: str
    explanation: str
    suggested_action: str
    priority_score: float = Field(ge=0, le=100)
    priority_level: str
    priority_breakdown: PriorityBreakdown
    sensitivity_analysis: list[PrioritySensitivityResult] = Field(default_factory=list)
    rule_version: str
    traceability: str


class DevelopmentMetadata(IntegrationModel):
    data_mode: str
    module2_source: str
    module3_source: str
    disclaimer: str
    recommendation_rule_version: str = "module4-prototype-rules-v2"
    priority_method: str = "Transparent prototype weighted sum."
    sensitivity_notice: str = "Exploratory sensitivity analysis; not validated research weights."


class Module4RecommendationResponse(IntegrationModel):
    employee_id: str
    employee_profile: EmployeeProfileSummary
    turnover_probability: float = Field(ge=0, le=1)
    risk_level: str
    eesi_score: float
    economic_pressure_level: str
    important_risk_factors: list[Module3RiskFactor]
    recommendations: list[PrioritizedRecommendation]
    metadata: DevelopmentMetadata
