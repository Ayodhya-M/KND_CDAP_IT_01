"""Application service coordinating Module 4's replaceable integrations."""

from app.module4.providers.base import Module2Provider, Module3Provider
from app.module4.repositories.employee_repository import EmployeeRepository
from app.module4.schemas.decision_support import (
    DevelopmentMetadata,
    EmployeeProfileSummary,
    Module4RecommendationResponse,
    PrioritizedRecommendation,
)
from app.module4.schemas.integration import Module4AnalysisInput
from app.module4.services.explanation_engine import ExplanationEngine
from app.module4.services.priority_engine import PriorityEngine
from app.module4.services.recommendation_engine import RecommendationEngine
from app.module4.services.risk_analyzer import RiskAnalyzer


MOCK_DISCLAIMER = (
    "Module 2 and Module 3 values are deterministic development fixtures, not "
    "calculated EESI results, model predictions, SHAP values, or validated research findings."
)


def provider_disclaimer(module2_is_mock: bool, module3_is_mock: bool, synthetic_demo: bool = False) -> str:
    if synthetic_demo:
        return ('Connected synthetic pilot demonstration: EESI is calculated and probabilities come from the saved synthetic model. '
                'Factors are positive probability differences under one-at-a-time probes (overtime off, satisfaction 4, or salary +10%), '
                'holding other model inputs, including EESI, fixed. These are not SHAP values or causal effects. '
                'Risk bands are unclassified. Recommendation priority uses prototype weights and continuous EESI/100, not validated thresholds. '
                'HIES household finances are not joined to these employees.')
    if module2_is_mock and module3_is_mock:
        return MOCK_DISCLAIMER
    mocked = []
    if module2_is_mock:
        mocked.append("Module 2")
    if module3_is_mock:
        mocked.append("Module 3")
    if mocked:
        return (
            f"{' and '.join(mocked)} values are deterministic development fixtures, not "
            "validated research findings, production predictions, or SHAP explanations."
        )
    return "Decision-support output; final HR decisions remain with authorized staff."


class RetentionDecisionService:
    """Run the proof-of-concept pipeline without depending on mock classes."""

    def __init__(
        self,
        employee_repository: EmployeeRepository,
        module2_provider: Module2Provider,
        module3_provider: Module3Provider,
        risk_analyzer: RiskAnalyzer | None = None,
        recommendation_engine: RecommendationEngine | None = None,
        priority_engine: PriorityEngine | None = None,
        explanation_engine: ExplanationEngine | None = None,
    ) -> None:
        self.employee_repository = employee_repository
        self.module2_provider = module2_provider
        self.module3_provider = module3_provider
        self.risk_analyzer = risk_analyzer or RiskAnalyzer()
        self.recommendation_engine = recommendation_engine or RecommendationEngine()
        self.priority_engine = priority_engine or PriorityEngine()
        self.explanation_engine = explanation_engine or ExplanationEngine()

    def recommendations_for_employee(
        self, employee_id: str, *, upload_id: str | None = None,
    ) -> Module4RecommendationResponse:
        return self.recommendations_for_analysis_input(
            self.analysis_input_for_employee(employee_id, upload_id=upload_id),
        )

    def analysis_input_for_employee(
        self, employee_id: str, *, upload_id: str | None = None,
    ) -> Module4AnalysisInput:
        """Load and validate the replaceable Module 1/2/3 integration boundary."""
        employee = self.employee_repository.get_employee_context(employee_id, upload_id=upload_id)
        economic_context = self.employee_repository.get_employee_economic_context(employee.id)
        eesi_result = self.module2_provider.get_eesi_result(employee, economic_context)
        prediction_result = self.module3_provider.get_prediction(employee, eesi_result)
        return Module4AnalysisInput(
            employee=employee,
            economic_context=economic_context,
            eesi_result=eesi_result,
            prediction_result=prediction_result,
        )

    def recommendations_for_analysis_input(
        self, analysis_input: Module4AnalysisInput,
    ) -> Module4RecommendationResponse:
        """Apply unchanged Module 4 logic to a validated integration input."""
        analysis = self.risk_analyzer.analyze(analysis_input)
        candidates = self.recommendation_engine.generate(analysis)
        is_mock = self.module2_provider.metadata.is_mock or self.module3_provider.metadata.is_mock

        recommendations: list[PrioritizedRecommendation] = []
        for candidate in candidates:
            priority = self.priority_engine.score(
                turnover_probability=analysis.turnover_probability,
                factor_contribution=candidate.factor_contribution,
                economic_pressure_level=analysis.economic_pressure_level,
                intervention_relevance=candidate.intervention_relevance,
                economic_pressure_score=analysis.eesi_score / 100 if self.module3_provider.metadata.data_mode == 'synthetic_demo_integration' else None,
            )
            recommendations.append(PrioritizedRecommendation(
                recommendation_id=candidate.recommendation_id,
                recommendation_type=candidate.recommendation_type,
                title=candidate.title,
                category=candidate.category,
                related_factor=candidate.related_factor,
                explanation=self.explanation_engine.explain(candidate, analysis, is_mock=is_mock),
                suggested_action=candidate.suggested_action,
                priority_score=priority.score,
                priority_level=priority.level,
            ))
        recommendations.sort(key=lambda item: item.priority_score, reverse=True)

        modes = {self.module2_provider.metadata.data_mode, self.module3_provider.metadata.data_mode}
        data_mode = modes.pop() if len(modes) == 1 else "mixed_integration"
        return Module4RecommendationResponse(
            employee_id=analysis.employee_id,
            employee_profile=EmployeeProfileSummary(
                department=analysis_input.employee.department,
                job_role=analysis_input.employee.job_role,
                job_level=analysis_input.employee.job_level,
                salary=float(analysis_input.employee.salary) if analysis_input.employee.salary is not None else None,
                overtime=analysis_input.employee.overtime,
                job_satisfaction=analysis_input.employee.job_satisfaction,
                work_life_balance=analysis_input.employee.work_life_balance,
                years_at_company=analysis_input.employee.years_at_company,
            ),
            turnover_probability=analysis.turnover_probability,
            risk_level=analysis.risk_level,
            eesi_score=analysis.eesi_score,
            economic_pressure_level=analysis.economic_pressure_level,
            important_risk_factors=analysis.important_factors,
            recommendations=recommendations,
            metadata=DevelopmentMetadata(
                data_mode=data_mode,
                module2_source=self.module2_provider.metadata.source,
                module3_source=self.module3_provider.metadata.source,
                disclaimer=provider_disclaimer(
                    self.module2_provider.metadata.is_mock,
                    self.module3_provider.metadata.is_mock,
                    synthetic_demo=self.module3_provider.metadata.data_mode == 'synthetic_demo_integration',
                ),
            ),
        )
