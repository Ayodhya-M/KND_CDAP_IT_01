from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.module4.config import PriorityWeights
from app.module4.providers.mock_module2_provider import MockModule2Provider
from app.module4.providers.mock_module3_provider import MockModule3Provider
from app.module4.schemas.decision_support import RecommendationCandidate, RiskAnalysis
from app.module4.schemas.integration import (
    Module1EmployeeContext,
    Module2EESIResult,
    Module3PredictionResult,
    Module3RiskFactor,
    Module4AnalysisInput,
)
from app.module4.services.explanation_engine import ExplanationEngine
from app.module4.services.priority_engine import PriorityEngine
from app.module4.services.recommendation_engine import RecommendationEngine
from app.module4.services.risk_analyzer import RiskAnalyzer


def employee(employee_id: str) -> Module1EmployeeContext:
    return Module1EmployeeContext(
        id=uuid4(),
        upload_id=uuid4(),
        employee_id=employee_id,
        age=34,
        salary=75000,
        department="Research",
        job_role="Analyst",
        job_level=2,
        business_travel="Travel_Rarely",
        distance_from_home=12,
        overtime=True,
        job_satisfaction=2,
        environment_satisfaction=3,
        work_life_balance=2,
        total_working_years=10,
        years_at_company=4,
        attrition=False,
        created_at=datetime.now(timezone.utc),
    )


def analysis(
    *, probability: float = 0.82, pressure: str = "High", factors: list[Module3RiskFactor] | None = None,
) -> RiskAnalysis:
    return RiskAnalysis(
        employee_id="EMP002",
        turnover_probability=probability,
        risk_level="High" if probability >= 0.7 else "Medium",
        eesi_score=0.78,
        economic_pressure_level=pressure,
        important_factors=factors or [],
    )


def test_mock_module2_has_deterministic_low_medium_high_fixtures() -> None:
    provider = MockModule2Provider()

    results = [provider.get_eesi_result(employee(identifier), None) for identifier in ("EMP003", "EMP001", "EMP002")]

    assert [(result.eesi_score, result.economic_pressure_level) for result in results] == [
        (0.25, "Low"), (0.55, "Medium"), (0.78, "High"),
    ]
    assert provider.metadata.is_mock is True


def test_mock_module3_has_deterministic_low_medium_high_fixtures() -> None:
    provider = MockModule3Provider()

    low = provider.get_prediction(employee("EMP003"))
    medium = provider.get_prediction(employee("EMP001"))
    high = provider.get_prediction(employee("EMP002"))

    assert (low.turnover_probability, low.risk_level, low.risk_factors) == (0.21, "Low", [])
    assert (medium.turnover_probability, medium.risk_level) == (0.56, "Medium")
    assert medium.risk_factors[0].feature_name == "job_satisfaction"
    assert (high.turnover_probability, high.risk_level) == (0.82, "High")
    assert high.risk_factors[0].feature_name == "overtime"
    assert high.risk_factors[0].feature_value is True


def test_risk_analyzer_preserves_and_orders_only_supplied_factors() -> None:
    person = employee("EMP002")
    supplied = [
        Module3RiskFactor(feature_name="work_life_balance", feature_value=2, contribution=0.16),
        Module3RiskFactor(feature_name="overtime", feature_value=True, contribution=0.24),
    ]
    boundary = Module4AnalysisInput(
        employee=person,
        eesi_result=Module2EESIResult(employee_id="EMP002", eesi_score=0.78, economic_pressure_level="High"),
        prediction_result=Module3PredictionResult(
            employee_id="EMP002", turnover_probability=0.82, risk_level="High", risk_factors=supplied,
        ),
    )

    result = RiskAnalyzer().analyze(boundary)

    assert [factor.feature_name for factor in result.important_factors] == ["overtime", "work_life_balance"]
    assert len(result.important_factors) == len(supplied)


def test_mismatching_employee_ids_are_rejected_at_integration_boundary() -> None:
    with pytest.raises(ValidationError, match="Module 3 employee_id does not match"):
        Module4AnalysisInput(
            employee=employee("EMP002"),
            eesi_result=Module2EESIResult(employee_id="EMP002", eesi_score=0.78, economic_pressure_level="High"),
            prediction_result=Module3PredictionResult(
                employee_id="DIFFERENT", turnover_probability=0.82, risk_level="High",
            ),
        )


def test_scenario_a_high_risk_overtime_creates_personalized_options() -> None:
    result = analysis(factors=[
        Module3RiskFactor(feature_name="overtime", feature_value=True, contribution=0.24),
    ])

    candidates = RecommendationEngine().generate(result)

    assert [item.title for item in candidates] == ["Overtime Review", "Flexible Scheduling"]
    assert all(item.related_factor == "overtime" for item in candidates)


def test_scenario_b_medium_risk_job_satisfaction_creates_engagement_options() -> None:
    result = analysis(
        probability=0.56,
        pressure="Medium",
        factors=[Module3RiskFactor(feature_name="job_satisfaction", feature_value=2, contribution=0.14)],
    )

    candidates = RecommendationEngine().generate(result)

    assert [item.title for item in candidates] == ["Employee Feedback Session", "Manager Check-in"]


def test_scenario_c_low_risk_without_actionable_factors_has_no_recommendations() -> None:
    result = analysis(probability=0.21, pressure="Low", factors=[])

    assert RecommendationEngine().generate(result) == []


def test_unsupported_and_non_positive_factors_do_not_generate_recommendations() -> None:
    result = analysis(factors=[
        Module3RiskFactor(feature_name="unsupported_feature", feature_value="x", contribution=0.9),
        Module3RiskFactor(feature_name="salary", feature_value=75000, contribution=-0.3),
    ])

    assert RecommendationEngine().generate(result) == []


def test_priority_engine_uses_documented_prototype_formula() -> None:
    result = PriorityEngine().score(
        turnover_probability=0.82,
        factor_contribution=0.24,
        economic_pressure_level="High",
        intervention_relevance=1.0,
    )

    assert result.score == 70.9
    assert result.level == "High"


def test_priority_weights_must_total_one() -> None:
    with pytest.raises(ValueError, match="total 1.0"):
        PriorityWeights(0.4, 0.3, 0.2, 0.2)


def test_explanation_is_mock_labelled_and_non_causal() -> None:
    candidate = RecommendationCandidate(
        recommendation_id="overtime_review",
        recommendation_type="overtime_review",
        title="Overtime Review",
        category="Work-Life Balance",
        related_factor="overtime",
        factor_value=True,
        factor_contribution=0.24,
        intervention_relevance=1,
        suggested_action="Review overtime.",
    )

    text = ExplanationEngine().explain(candidate, analysis(), is_mock=True)

    assert "mock development prediction explanation" in text
    assert "does not establish" in text
    assert "will resign" not in text
