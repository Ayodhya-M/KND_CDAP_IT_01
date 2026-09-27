"""Non-causal, human-readable recommendation explanations."""

from app.module4.schemas.decision_support import RecommendationCandidate, RiskAnalysis


class ExplanationEngine:
    def explain(
        self,
        recommendation: RecommendationCandidate,
        analysis: RiskAnalysis,
        *,
        is_mock: bool,
    ) -> str:
        source_phrase = "mock development prediction explanation" if is_mock else "current prediction explanation"
        pressure = analysis.economic_pressure_level
        return (
            f"{recommendation.related_factor} is an important factor in the {source_phrase} "
            f"and is associated with the current model-based risk assessment. The current economic "
            f"pressure result is {pressure}. HR may consider {recommendation.title.lower()} as a "
            "decision-support option; this does not establish that the factor causes turnover or "
            "that the action will prevent resignation."
        )
