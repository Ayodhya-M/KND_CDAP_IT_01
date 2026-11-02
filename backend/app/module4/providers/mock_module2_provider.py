"""Development-only Module 2 fixture provider.

These values are not calculated EESI results. The 0-1 score range, scenario
values, and labels are provisional fixtures and require replacement with the
real Module 2 integration and scientifically defined contract.
"""

from app.module4.providers.base import ProviderMetadata
from app.module4.providers.mock_scenarios import MockScenario, scenario_for_employee
from app.module4.schemas.integration import (
    Module1EconomicContext,
    Module1EmployeeContext,
    Module2EESIResult,
)


_SCENARIOS: dict[MockScenario, tuple[float, str]] = {
    MockScenario.LOW: (0.25, "Low"),
    MockScenario.MEDIUM: (0.55, "Medium"),
    MockScenario.HIGH: (0.78, "High"),
}


class MockModule2Provider:
    """Return deterministic EESI-shaped fixtures without calculating EESI."""

    metadata = ProviderMetadata(source="mock", data_mode="mock_integration", is_mock=True)

    def get_eesi_result(
        self,
        employee: Module1EmployeeContext,
        economic_context: Module1EconomicContext | None,
    ) -> Module2EESIResult:
        del economic_context  # The mock must not calculate EESI from Module 1 data.
        score, level = _SCENARIOS[scenario_for_employee(employee.employee_id)]
        return Module2EESIResult(
            employee_id=employee.employee_id,
            eesi_score=score,
            economic_pressure_level=level,
        )
