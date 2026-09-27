"""Transparent prototype scoring for ordering recommendation candidates."""

from dataclasses import dataclass

from app.module4.config import (
    PROTOTYPE_HIGH_PRIORITY_THRESHOLD,
    PROTOTYPE_MEDIUM_PRIORITY_THRESHOLD,
    PROTOTYPE_PRESSURE_SCORES,
    PROTOTYPE_PRIORITY_WEIGHTS,
    PriorityWeights,
)


@dataclass(frozen=True)
class PriorityResult:
    score: float
    level: str


class PriorityEngine:
    """Apply configurable prototype weights; no outcome effectiveness is implied."""

    def __init__(self, weights: PriorityWeights = PROTOTYPE_PRIORITY_WEIGHTS) -> None:
        self.weights = weights

    def score(
        self,
        *,
        turnover_probability: float,
        factor_contribution: float,
        economic_pressure_level: str,
        intervention_relevance: float,
    ) -> PriorityResult:
        risk = self._unit(turnover_probability)
        contribution = self._unit(abs(factor_contribution))
        pressure = PROTOTYPE_PRESSURE_SCORES.get(economic_pressure_level.strip().lower(), 0.0)
        relevance = self._unit(intervention_relevance)
        raw_score = (
            risk * self.weights.turnover_risk
            + contribution * self.weights.factor_contribution
            + pressure * self.weights.economic_pressure
            + relevance * self.weights.intervention_relevance
        )
        score = round(raw_score * 100, 2)
        if score >= PROTOTYPE_HIGH_PRIORITY_THRESHOLD:
            level = "High"
        elif score >= PROTOTYPE_MEDIUM_PRIORITY_THRESHOLD:
            level = "Medium"
        else:
            level = "Low"
        return PriorityResult(score=score, level=level)

    @staticmethod
    def _unit(value: float) -> float:
        return max(0.0, min(1.0, value))
