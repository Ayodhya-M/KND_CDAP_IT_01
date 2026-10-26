"""Prototype research configuration for Module 4.

These values support proof-of-concept evaluation only. They are not validated
research constants and must remain configurable for later expert validation.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class PriorityWeights:
    turnover_risk: float = 0.35
    factor_contribution: float = 0.30
    economic_pressure: float = 0.20
    intervention_relevance: float = 0.15

    def __post_init__(self) -> None:
        values = (
            self.turnover_risk,
            self.factor_contribution,
            self.economic_pressure,
            self.intervention_relevance,
        )
        if any(value < 0 for value in values):
            raise ValueError("Priority weights cannot be negative")
        if abs(sum(values) - 1.0) > 1e-9:
            raise ValueError("Priority weights must total 1.0")


PROTOTYPE_PRIORITY_WEIGHTS = PriorityWeights()
PROTOTYPE_PRESSURE_SCORES = {"low": 0.25, "medium": 0.60, "high": 1.0}
PROTOTYPE_MEDIUM_PRIORITY_THRESHOLD = 40.0
PROTOTYPE_HIGH_PRIORITY_THRESHOLD = 70.0
