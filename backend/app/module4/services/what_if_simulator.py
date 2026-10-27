"""Illustrative scenario comparison without database writes or fake predictions."""

from app.module4.schemas.integration import (
    Module1EmployeeContext,
    Module3PredictionResult,
    Module3RiskFactor,
    Module4AnalysisInput,
)
from app.module4.schemas.simulation import (
    ScenarioValues,
    WhatIfChanges,
    WhatIfSimulationResponse,
)
from app.module4.services.decision_service import RetentionDecisionService


class WhatIfSimulator:
    """Re-evaluate rule applicability against an in-memory employee scenario.

    This deliberately does not estimate a new turnover probability. It can only
    remove an existing mock-supplied factor when a documented prototype rule no
    longer applies; it never creates a new risk factor or persists employee data.
    """

    def __init__(self, decision_service: RetentionDecisionService) -> None:
        self.decision_service = decision_service

    def simulate(
        self, employee_id: str, changes: WhatIfChanges, *, upload_id: str | None = None,
    ) -> WhatIfSimulationResponse:
        original_input = self.decision_service.analysis_input_for_employee(employee_id, upload_id=upload_id)
        original = self.decision_service.recommendations_for_analysis_input(original_input)
        updates = changes.model_dump(exclude_none=True)
        employee_data = original_input.employee.model_dump()
        employee_data.update(updates)
        simulated_employee = Module1EmployeeContext.model_validate(employee_data)
        if self.decision_service.module3_provider.metadata.data_mode == 'synthetic_demo_integration':
            eesi = self.decision_service.module2_provider.get_eesi_result(simulated_employee, original_input.economic_context)
            prediction = self.decision_service.module3_provider.get_scenario_prediction(simulated_employee, eesi)
            scenario_input = Module4AnalysisInput(employee=simulated_employee,
                economic_context=original_input.economic_context, eesi_result=eesi, prediction_result=prediction)
            simulated = self.decision_service.recommendations_for_analysis_input(scenario_input)
            old_factors = {factor.feature_name for factor in original_input.prediction_result.risk_factors}
            new_factors = {factor.feature_name for factor in prediction.risk_factors}
            return WhatIfSimulationResponse(employee_id=employee_id,
                original_values=self._scenario_values(original_input.employee),
                simulated_values=self._scenario_values(simulated_employee),
                original_turnover_probability=original.turnover_probability,
                simulated_turnover_probability=simulated.turnover_probability,
                probability_difference=round(100 * (simulated.turnover_probability - original.turnover_probability), 6),
                original_recommendations=original.recommendations,
                simulated_recommendations=simulated.recommendations,
                removed_risk_factors=sorted(old_factors - new_factors),
                retained_risk_factors=sorted(old_factors & new_factors),
                assumptions=['EESI and the synthetic model are recalculated with temporary employee inputs.',
                             'Economic context remains fixed; probability differences are percentage points.',
                             'Work-life balance is not a feature of this saved model and cannot directly affect its prediction.',
                             'Input sensitivities are model diagnostics, not intervention effects or SHAP values.',
                             'No employee data or model artifacts are modified.'],
                disclaimer='Synthetic-model scenario only; changes do not establish causality, intervention effectiveness or future resignation risk.',
                metadata=simulated.metadata)

        retained: list[Module3RiskFactor] = []
        removed: list[str] = []
        for factor in original_input.prediction_result.risk_factors:
            value = updates.get(factor.feature_name, factor.feature_value)
            applies = self._factor_still_applies(factor.feature_name, value)
            if applies:
                retained.append(Module3RiskFactor(
                    feature_name=factor.feature_name,
                    feature_value=value,
                    contribution=factor.contribution,
                ))
            else:
                removed.append(factor.feature_name)

        prediction_data = original_input.prediction_result.model_dump()
        prediction_data["risk_factors"] = retained
        simulated_input = Module4AnalysisInput(
            employee=simulated_employee,
            economic_context=original_input.economic_context,
            eesi_result=original_input.eesi_result,
            prediction_result=Module3PredictionResult.model_validate(prediction_data),
        )
        simulated = self.decision_service.recommendations_for_analysis_input(simulated_input)

        return WhatIfSimulationResponse(
            employee_id=employee_id,
            original_values=self._scenario_values(original_input.employee),
            simulated_values=self._scenario_values(simulated_employee),
            original_turnover_probability=original.turnover_probability,
            simulated_turnover_probability=original.turnover_probability,
            probability_difference=0.0,
            original_recommendations=original.recommendations,
            simulated_recommendations=simulated.recommendations,
            removed_risk_factors=removed,
            retained_risk_factors=[factor.feature_name for factor in retained],
            assumptions=[
                "The mock turnover probability and risk level are held constant; this is not a forecast.",
                "Only risk factors supplied by Module 3 are considered, and no new factors are inferred.",
                "Prototype contribution values remain unchanged when recommendations are re-ranked.",
                "Overtime is inapplicable when set to false; satisfaction factors are inapplicable above level 2.",
                "No approved salary threshold exists, so salary changes are displayed but do not add or remove a factor.",
                "Scenario changes are evaluated in memory and are not saved to Module 1 or Supabase.",
            ],
            disclaimer=(
                "This comparison illustrates recommendation-rule behavior only. It does not establish causality, "
                "intervention effectiveness, or a changed probability of resignation."
            ),
            metadata=simulated.metadata,
        )

    @staticmethod
    def _factor_still_applies(feature_name: str, value: object) -> bool:
        if feature_name == "overtime" and value is False:
            return False
        if feature_name in {"job_satisfaction", "work_life_balance"}:
            return not isinstance(value, int) or isinstance(value, bool) or value <= 2
        return True

    @staticmethod
    def _scenario_values(employee: Module1EmployeeContext) -> ScenarioValues:
        return ScenarioValues(
            salary=float(employee.salary) if employee.salary is not None else None,
            overtime=employee.overtime,
            job_satisfaction=employee.job_satisfaction,
            work_life_balance=employee.work_life_balance,
        )
