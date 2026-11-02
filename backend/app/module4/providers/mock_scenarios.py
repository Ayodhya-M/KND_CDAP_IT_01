"""Deterministic scenario selection shared by development-only providers."""

from enum import Enum


class MockScenario(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


def scenario_for_employee(employee_id: str) -> MockScenario:
    """Assign a repeatable fixture scenario; this is not a research calculation.

    Numeric identifiers cycle through low, medium, and high fixtures. Identifiers
    without digits use a stable character sum. This selection exists only to
    make progress-presentation demonstrations reproducible.
    """
    digits = "".join(character for character in employee_id if character.isdigit())
    selector = int(digits) if digits else sum(ord(character) for character in employee_id)
    return (MockScenario.LOW, MockScenario.MEDIUM, MockScenario.HIGH)[selector % 3]
