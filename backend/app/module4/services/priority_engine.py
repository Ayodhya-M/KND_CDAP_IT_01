"""Transparent prototype scoring for ordering recommendation candidates."""

from dataclasses import dataclass

from app.module4.config import (
    PROTOTYPE_HIGH_PRIORITY_THRESHOLD,
    PROTOTYPE_MEDIUM_PRIORITY_THRESHOLD,
    PROTOTYPE_PRESSURE_SCORES,
    PROTOTYPE_PRIORITY_WEIGHTS,
    PROTOTYPE_SENSITIVITY_DELTA,
    PriorityWeights,
)
from app.module4.schemas.decision_support import PriorityBreakdown, PriorityValues


@dataclass(frozen=True)
class PriorityResult:
    score: float
    level: str
    breakdown: PriorityBreakdown


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
        economic_pressure_score: float | None = None,
    ) -> PriorityResult:
        risk = self._unit(turnover_probability)
        contribution = self._unit(abs(factor_contribution))
        pressure = PROTOTYPE_PRESSURE_SCORES.get(economic_pressure_level.strip().lower(), 0.0)
        if economic_pressure_score is not None:
            pressure = self._unit(economic_pressure_score)
        relevance = self._unit(intervention_relevance)
        inputs = PriorityValues(
            turnover_risk=risk,
            factor_contribution=contribution,
            economic_pressure=pressure,
            intervention_relevance=relevance,
        )
        weights = PriorityValues(**self.weights.__dict__)
        components = PriorityValues(
            turnover_risk=risk * self.weights.turnover_risk,
            factor_contribution=contribution * self.weights.factor_contribution,
            economic_pressure=pressure * self.weights.economic_pressure,
            intervention_relevance=relevance * self.weights.intervention_relevance,
        )
        raw_score = sum(components.model_dump().values())
        score = round(raw_score * 100, 2)
        if score >= PROTOTYPE_HIGH_PRIORITY_THRESHOLD:
            level = "High"
        elif score >= PROTOTYPE_MEDIUM_PRIORITY_THRESHOLD:
            level = "Medium"
        else:
            level = "Low"
        return PriorityResult(
            score=score,
            level=level,
            breakdown=PriorityBreakdown(
                formula="100 × Σ(normalized input × prototype weight)",
                inputs=inputs,
                weights=weights,
                weighted_components=components,
                raw_weighted_total=raw_score,
                score=score,
            ),
        )

    def exploratory_weight_scenarios(self) -> list[tuple[str, str, PriorityWeights]]:
        """Return small deterministic perturbations, not validated alternatives."""
        base = self.weights.__dict__
        scenarios = []
        for emphasized in base:
            increase = min(PROTOTYPE_SENSITIVITY_DELTA, 1.0 - base[emphasized])
            other_total = 1.0 - base[emphasized]
            if increase <= 0 or other_total <= 0:
                continue
            values = {
                name: (value + increase if name == emphasized else value - increase * value / other_total)
                for name, value in base.items()
            }
            scenarios.append((
                f"emphasize_{emphasized}",
                f"Exploratory +{increase:.2f} emphasis on {emphasized.replace('_', ' ')}",
                PriorityWeights(**values),
            ))
        return scenarios

    @staticmethod
    def _unit(value: float) -> float:
        return max(0.0, min(1.0, value))
