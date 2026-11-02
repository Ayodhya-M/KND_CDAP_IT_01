"""Initial transparent mapping from supported risk factors to HR options."""

from dataclasses import dataclass

from app.module4.schemas.decision_support import RecommendationCandidate, RiskAnalysis


RECOMMENDATION_RULE_VERSION = "module4-prototype-rules-v2"


@dataclass(frozen=True)
class RecommendationRule:
    recommendation_id: str
    title: str
    category: str
    suggested_action: str
    relevance: float


# Prototype mappings include only verified Module 1 fields. Protected personal
# characteristics are intentionally absent. These rules require later research
# literature and HR/expert validation.
PROTOTYPE_RULES: dict[str, tuple[RecommendationRule, ...]] = {
    "overtime": (
        RecommendationRule(
            "overtime_review", "Overtime Review", "Work-Life Balance",
            "Review the employee's overtime requirements and consider workload or scheduling adjustments.", 1.0,
        ),
        RecommendationRule(
            "flexible_scheduling", "Flexible Scheduling", "Work-Life Balance",
            "Discuss whether a practical scheduling adjustment may be considered under organizational policy.", 0.85,
        ),
    ),
    "job_satisfaction": (
        RecommendationRule(
            "employee_feedback_session", "Employee Feedback Session", "Engagement",
            "Invite the employee to a confidential discussion about their work experience and concerns.", 1.0,
        ),
        RecommendationRule(
            "manager_check_in", "Manager Check-in", "Wellbeing",
            "Arrange a supportive manager check-in focused on listening and appropriate follow-up.", 0.85,
        ),
    ),
    "work_life_balance": (
        RecommendationRule(
            "work_life_balance_support", "Work-Life Balance Support", "Wellbeing",
            "Review available work-life balance support with the employee.", 1.0,
        ),
        RecommendationRule(
            "flexible_work_arrangement", "Flexible Work Arrangement", "Wellbeing",
            "Discuss whether an appropriate flexible work arrangement is permitted and suitable.", 0.85,
        ),
    ),
    "environment_satisfaction": (
        RecommendationRule(
            "workplace_environment_review", "Workplace Environment Review", "Work Environment",
            "Discuss workplace-environment concerns and identify issues HR may appropriately review.", 0.90,
        ),
    ),
    "business_travel": (
        RecommendationRule(
            "business_travel_review", "Business Travel Review", "Work Arrangement",
            "Review business-travel expectations and discuss feasible adjustments where policy permits.", 0.85,
        ),
    ),
    "distance_from_home": (
        RecommendationRule(
            "hybrid_work_discussion", "Flexible/Hybrid Work Discussion", "Work Arrangement",
            "Discuss flexible or hybrid work options only where the role and organizational policy permit.", 0.80,
        ),
    ),
    "salary": (
        RecommendationRule(
            "compensation_review", "Compensation Review", "Compensation",
            "Review compensation through the organization's normal, equitable HR process.", 0.95,
        ),
    ),
}


class RecommendationEngine:
    """Generate candidates only for positive, supported supplied factors."""

    def generate(self, analysis: RiskAnalysis) -> list[RecommendationCandidate]:
        recommendations: list[RecommendationCandidate] = []
        for factor in analysis.important_factors:
            if factor.contribution <= 0:
                continue
            eligibility = self._eligibility_basis(factor.feature_name, factor.feature_value)
            if eligibility is None:
                continue
            for rule in PROTOTYPE_RULES.get(factor.feature_name, ()):
                recommendations.append(RecommendationCandidate(
                    recommendation_id=rule.recommendation_id,
                    recommendation_type=rule.recommendation_id,
                    title=rule.title,
                    category=rule.category,
                    related_factor=factor.feature_name,
                    factor_value=factor.feature_value,
                    factor_contribution=factor.contribution,
                    intervention_relevance=rule.relevance,
                    suggested_action=rule.suggested_action,
                    rule_version=RECOMMENDATION_RULE_VERSION,
                    eligibility_basis=eligibility,
                ))
        return recommendations

    @staticmethod
    def _eligibility_basis(feature_name: str, value: object) -> str | None:
        """Reject only contradictions supported by verified field semantics."""
        if feature_name == "overtime":
            if value is False or (isinstance(value, str) and value.strip().lower() in {"no", "false", "0"}):
                return None
            return "Positive overtime factor supplied by Module 3 and current value is not explicitly No."
        if feature_name in {"job_satisfaction", "work_life_balance"}:
            if isinstance(value, int) and not isinstance(value, bool) and value > 2:
                return None
            return "Positive satisfaction-related factor supplied by Module 3; verified value is not above the documented prototype level 2 boundary."
        if feature_name == "business_travel":
            if isinstance(value, str) and value.strip().lower() == "non-travel":
                return None
            return "Positive business-travel factor supplied by Module 3 and current value is not Non-Travel."
        if feature_name == "distance_from_home":
            if isinstance(value, (int, float)) and not isinstance(value, bool) and value <= 0:
                return None
            return "Positive distance factor supplied by Module 3 and recorded distance is greater than zero or unavailable."
        if feature_name == "salary":
            if isinstance(value, (int, float)) and not isinstance(value, bool) and value <= 0:
                return None
            return "Positive salary factor supplied by Module 3; no salary threshold is inferred by Module 4."
        return "Positive supported factor supplied by Module 3; Module 4 does not infer an additional threshold."
