from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.module4.config import PROTOTYPE_PRIORITY_WEIGHTS
from app.module4.providers.mock_module2_provider import MockModule2Provider
from app.module4.providers.mock_module3_provider import MockModule3Provider
from app.module4.schemas.decision_support import RiskAnalysis
from app.module4.schemas.integration import Module1EmployeeContext, Module3RiskFactor
from app.module4.services.decision_service import RetentionDecisionService
from app.module4.services.priority_engine import PriorityEngine
from app.module4.services.recommendation_engine import (
    RECOMMENDATION_RULE_VERSION,
    RecommendationEngine,
)


def employee() -> Module1EmployeeContext:
    return Module1EmployeeContext(
        id=uuid4(), upload_id=uuid4(), employee_id="PILOT-0002", age=31,
        salary=75000, department="Sales", job_level=2, overtime=True,
        job_satisfaction=2, work_life_balance=2, years_at_company=4,
        attrition=False, created_at=datetime.now(timezone.utc),
    )


class Repository:
    def __init__(self) -> None:
        self.person = employee()

    def get_employee_context(self, *_args, **_kwargs):
        return self.person

    def get_employee_economic_context(self, *_args):
        return None


def analysis(feature_name: str, value: object) -> RiskAnalysis:
    return RiskAnalysis(
        employee_id="PILOT-0002", turnover_probability=0.82,
        risk_level="High", eesi_score=0.78, economic_pressure_level="High",
        important_factors=[Module3RiskFactor(
            feature_name=feature_name, feature_value=value, contribution=0.24,
        )],
    )


def test_priority_breakdown_preserves_prototype_score_and_formula() -> None:
    result = PriorityEngine().score(
        turnover_probability=0.82, factor_contribution=0.24,
        economic_pressure_level="High", intervention_relevance=1.0,
    )

    assert result.score == 70.9
    assert result.breakdown.score == result.score
    assert result.breakdown.inputs.model_dump() == {
        "turnover_risk": 0.82,
        "factor_contribution": 0.24,
        "economic_pressure": 1.0,
        "intervention_relevance": 1.0,
    }
    assert result.breakdown.weights.model_dump() == PROTOTYPE_PRIORITY_WEIGHTS.__dict__
    assert sum(result.breakdown.weighted_components.model_dump().values()) == pytest.approx(0.709)


def test_exploratory_weight_scenarios_are_small_normalized_perturbations() -> None:
    scenarios = PriorityEngine().exploratory_weight_scenarios()

    assert len(scenarios) == 4
    assert {scenario_id for scenario_id, _, _ in scenarios} == {
        "emphasize_turnover_risk", "emphasize_factor_contribution",
        "emphasize_economic_pressure", "emphasize_intervention_relevance",
    }
    for _, label, weights in scenarios:
        assert label.startswith("Exploratory +0.05")
        assert sum(weights.__dict__.values()) == pytest.approx(1.0)


@pytest.mark.parametrize(
    ("feature_name", "value"),
    [
        ("overtime", False),
        ("overtime", "No"),
        ("job_satisfaction", 4),
        ("work_life_balance", 3),
        ("business_travel", "Non-Travel"),
        ("distance_from_home", 0),
        ("salary", 0),
    ],
)
def test_context_inappropriate_recommendations_are_suppressed(feature_name: str, value: object) -> None:
    assert RecommendationEngine().generate(analysis(feature_name, value)) == []


def test_supported_positive_factor_retains_versioned_traceability() -> None:
    recommendations = RecommendationEngine().generate(analysis("overtime", True))

    assert [item.recommendation_id for item in recommendations] == [
        "overtime_review", "flexible_scheduling",
    ]
    assert all(item.rule_version == RECOMMENDATION_RULE_VERSION for item in recommendations)
    assert all("current value is not explicitly No" in item.eligibility_basis for item in recommendations)


def test_decision_response_contains_breakdowns_sensitivity_ranks_and_rule_metadata() -> None:
    result = RetentionDecisionService(
        Repository(), MockModule2Provider(), MockModule3Provider(),
    ).recommendations_for_employee("PILOT-0002")

    assert result.metadata.recommendation_rule_version == RECOMMENDATION_RULE_VERSION
    assert "prototype weighted sum" in result.metadata.priority_method.lower()
    assert "not validated alternatives" in result.metadata.sensitivity_notice
    assert result.recommendations
    for recommendation in result.recommendations:
        assert recommendation.priority_breakdown.score == recommendation.priority_score
        assert recommendation.rule_version == RECOMMENDATION_RULE_VERSION
        assert recommendation.recommendation_id in recommendation.traceability
        assert len(recommendation.sensitivity_analysis) == 4
        assert all(1 <= item.rank <= len(result.recommendations) for item in recommendation.sensitivity_analysis)

