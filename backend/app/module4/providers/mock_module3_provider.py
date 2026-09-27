"""Development-only Module 3 fixture provider.

No model is trained or executed here. Contributions are mock feature-importance
fixtures, not SHAP values or validated production explanations. Replace this
provider with the real Module 3 prediction adapter when its contract is ready.
"""

from app.module4.providers.base import ProviderMetadata
from app.module4.providers.mock_scenarios import MockScenario, scenario_for_employee
from app.module4.schemas.integration import (
    Module1EmployeeContext,
    Module3PredictionResult,
    Module3RiskFactor,
)


class MockModule3Provider:
    """Return deterministic prediction-shaped fixtures for integration tests."""

    metadata = ProviderMetadata(source="mock", data_mode="mock_integration", is_mock=True)

    def get_prediction(self, employee: Module1EmployeeContext) -> Module3PredictionResult:
        scenario = scenario_for_employee(employee.employee_id)
        if scenario is MockScenario.HIGH:
            return Module3PredictionResult(
                employee_id=employee.employee_id,
                turnover_probability=0.82,
                risk_level="High",
                risk_factors=[
                    Module3RiskFactor(
                        feature_name="overtime",
                        feature_value=employee.overtime,
                        contribution=0.24,
                    ),
                    Module3RiskFactor(
                        feature_name="job_satisfaction",
                        feature_value=employee.job_satisfaction,
                        contribution=0.19,
                    ),
                    Module3RiskFactor(
                        feature_name="work_life_balance",
                        feature_value=employee.work_life_balance,
                        contribution=0.16,
                    ),
                ],
            )
        if scenario is MockScenario.MEDIUM:
            return Module3PredictionResult(
                employee_id=employee.employee_id,
                turnover_probability=0.56,
                risk_level="Medium",
                risk_factors=[
                    Module3RiskFactor(
                        feature_name="job_satisfaction",
                        feature_value=employee.job_satisfaction,
                        contribution=0.14,
                    )
                ],
            )
        return Module3PredictionResult(
            employee_id=employee.employee_id,
            turnover_probability=0.21,
            risk_level="Low",
            risk_factors=[],
        )
