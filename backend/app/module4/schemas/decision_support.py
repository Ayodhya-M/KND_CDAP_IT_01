"""Validated outputs produced by the Module 4 proof-of-concept services."""

from typing import Any

from pydantic import Field

from app.module4.schemas.integration import IntegrationModel, Module3RiskFactor


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


class DevelopmentMetadata(IntegrationModel):
    data_mode: str
    module2_source: str
    module3_source: str
    disclaimer: str


class Module4RecommendationResponse(IntegrationModel):
    employee_id: str
    turnover_probability: float = Field(ge=0, le=1)
    risk_level: str
    eesi_score: float
    economic_pressure_level: str
    important_risk_factors: list[Module3RiskFactor]
    recommendations: list[PrioritizedRecommendation]
    metadata: DevelopmentMetadata
