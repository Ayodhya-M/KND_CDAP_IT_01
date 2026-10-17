"""Preparation adapter for Module 3's saved prediction pipeline."""

from collections.abc import Callable
from typing import Any

from app.module4.providers.base import ProviderMetadata, ProviderResultUnavailableError
from app.module4.schemas.integration import (
    Module1EmployeeContext,
    Module2EESIResult,
    Module3PredictionResult,
    Module3RiskFactor,
)
from app.services.module3_prediction import get_model_status, predict_saved_model


RiskLevelResolver = Callable[[float], str]
RiskFactorResolver = Callable[
    [Module1EmployeeContext, dict[str, Any], dict[str, Any]], list[Module3RiskFactor]
]


class RealModule3Provider:
    """Map stable Module 4 inputs to Module 3 without inventing missing contracts."""

    metadata = ProviderMetadata(source="module3", data_mode="integrated", is_mock=False)

    def __init__(
        self,
        *,
        positive_class_label: str | None,
        risk_level_resolver: RiskLevelResolver | None = None,
        risk_factor_resolver: RiskFactorResolver | None = None,
    ) -> None:
        self.positive_class_label = positive_class_label.strip() if positive_class_label else None
        self.risk_level_resolver = risk_level_resolver
        self.risk_factor_resolver = risk_factor_resolver

    @staticmethod
    def build_feature_record(
        employee: Module1EmployeeContext,
        eesi_result: Module2EESIResult,
    ) -> dict[str, Any]:
        overtime: str | None
        if employee.overtime is None:
            overtime = None
        else:
            overtime = "Yes" if employee.overtime else "No"
        return {
            "Age": employee.age,
            "MonthlyIncome": float(employee.salary) if employee.salary is not None else None,
            "OverTime": overtime,
            "JobSatisfaction": employee.job_satisfaction,
            "JobLevel": employee.job_level,
            "YearsAtCompany": employee.years_at_company,
            "Department": employee.department,
            "EESI": eesi_result.eesi_score,
        }

    @staticmethod
    def extract_positive_probability(
        prediction: dict[str, Any], positive_class_label: str
    ) -> float:
        probabilities = prediction.get("class_probabilities")
        if not isinstance(probabilities, dict) or positive_class_label not in probabilities:
            raise ProviderResultUnavailableError(
                f"Module 3 did not return the verified positive class '{positive_class_label}'"
            )
        probability = float(probabilities[positive_class_label])
        if not 0 <= probability <= 1:
            raise ProviderResultUnavailableError("Module 3 returned an invalid turnover probability")
        return probability

    def get_prediction(
        self,
        employee: Module1EmployeeContext,
        eesi_result: Module2EESIResult,
    ) -> Module3PredictionResult:
        if self.positive_class_label is None:
            raise ProviderResultUnavailableError(
                "Module 3 real provider is unavailable: positive attrition class is not configured"
            )
        if eesi_result.score_scale != "0-100" or not eesi_result.formula_identifier or not eesi_result.formula_version:
            raise ProviderResultUnavailableError(
                "Module 3 real provider is unavailable: a selected 0-100 Module 2 EESI result with formula provenance is required"
            )
        status = get_model_status()
        if not status.get("model_available"):
            raise ProviderResultUnavailableError(
                f"Module 3 real provider is unavailable: {status.get('message', 'model artifact is missing')}"
            )
        classes = [str(value) for value in status.get("classes", [])]
        if self.positive_class_label not in classes:
            raise ProviderResultUnavailableError(
                f"Module 3 real provider is unavailable: configured positive class '{self.positive_class_label}' is not in the saved model classes"
            )
        feature_record = self.build_feature_record(employee, eesi_result)
        saved_features = status.get("feature_columns", [])
        if list(saved_features) != list(feature_record):
            raise ProviderResultUnavailableError(
                "Module 3 real provider is unavailable: saved model feature contract does not match the Module 1/2 adapter"
            )
        eesi_integration = status.get("eesi_integration")
        if not isinstance(eesi_integration, dict) or not eesi_integration.get("enabled"):
            raise ProviderResultUnavailableError(
                "Module 3 real provider is unavailable: saved model does not declare EESI integration provenance"
            )
        if (
            eesi_integration.get("formula_id") != eesi_result.formula_identifier
            or eesi_integration.get("formula_version") != eesi_result.formula_version
        ):
            raise ProviderResultUnavailableError(
                "Module 3 real provider is unavailable: EESI formula provenance does not match the saved model"
            )
        missing_contracts = []
        if self.risk_level_resolver is None:
            missing_contracts.append("risk classification")
        if self.risk_factor_resolver is None:
            missing_contracts.append("feature explanation")
        if missing_contracts:
            raise ProviderResultUnavailableError(
                "Module 3 real provider is unavailable: approved " + " and ".join(missing_contracts) + " contracts are missing"
            )

        prediction = predict_saved_model(feature_record)
        probability = self.extract_positive_probability(prediction, self.positive_class_label)
        risk_level = self.risk_level_resolver(probability)
        risk_factors = self.risk_factor_resolver(employee, prediction, status)
        return Module3PredictionResult(
            employee_id=employee.employee_id,
            turnover_probability=probability,
            risk_level=risk_level,
            risk_factors=risk_factors,
            model_name=status.get("model_name"),
            model_version=status.get("model_version"),
            model_dataset_kind=status.get("dataset_kind"),
            positive_class_label=self.positive_class_label,
            eesi_formula_identifier=eesi_result.formula_identifier,
            eesi_formula_version=eesi_result.formula_version,
        )
