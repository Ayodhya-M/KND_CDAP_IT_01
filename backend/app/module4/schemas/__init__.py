"""Validated data contracts used by Module 4."""

from app.module4.schemas.decision_support import (
    DevelopmentMetadata,
    Module4RecommendationResponse,
    PrioritizedRecommendation,
    RecommendationCandidate,
    RiskAnalysis,
)
from app.module4.schemas.integration import (
    Module1EconomicContext,
    Module1EmployeeContext,
    Module2EESIResult,
    Module3PredictionResult,
    Module3RiskFactor,
    Module4AnalysisInput,
)

__all__ = [
    "DevelopmentMetadata",
    "Module1EconomicContext",
    "Module1EmployeeContext",
    "Module2EESIResult",
    "Module3PredictionResult",
    "Module3RiskFactor",
    "Module4AnalysisInput",
    "Module4RecommendationResponse",
    "PrioritizedRecommendation",
    "RecommendationCandidate",
    "RiskAnalysis",
]
