"""Combine validated upstream contexts without creating new risk factors."""

from app.module4.schemas.decision_support import RiskAnalysis
from app.module4.schemas.integration import Module4AnalysisInput


class RiskAnalyzer:
    """Expose Module 3's supplied factors in consistent importance order."""

    def analyze(self, analysis_input: Module4AnalysisInput) -> RiskAnalysis:
        factors = sorted(
            analysis_input.prediction_result.risk_factors,
            key=lambda factor: abs(factor.contribution),
            reverse=True,
        )
        return RiskAnalysis(
            employee_id=analysis_input.employee.employee_id,
            turnover_probability=analysis_input.prediction_result.turnover_probability,
            risk_level=analysis_input.prediction_result.risk_level,
            eesi_score=analysis_input.eesi_result.eesi_score,
            economic_pressure_level=analysis_input.eesi_result.economic_pressure_level,
            important_factors=factors,
        )
