from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from app.config import Settings
from app.module4.providers.base import ProviderResultUnavailableError
from app.module4.providers.mock_module2_provider import MockModule2Provider
from app.module4.providers.mock_module3_provider import MockModule3Provider
from app.module4.providers.real_module2_provider import RealModule2Provider
from app.module4.providers.real_module3_provider import RealModule3Provider
from app.module4.routers.recommendations import build_module2_provider, build_module3_provider
from app.module4.schemas.integration import Module1EconomicContext, Module1EmployeeContext, Module2EESIResult


def employee(**changes) -> Module1EmployeeContext:
    values = {
        "id": uuid4(),
        "upload_id": uuid4(),
        "employee_id": "PILOT-0002",
        "age": 31,
        "salary": Decimal("75000"),
        "department": "Sales",
        "job_level": 2,
        "overtime": True,
        "job_satisfaction": 2,
        "years_at_company": 4,
        "attrition": False,
        "created_at": datetime.now(timezone.utc),
    }
    values.update(changes)
    return Module1EmployeeContext(**values)


def economic(**changes) -> Module1EconomicContext:
    values = {
        "id": uuid4(),
        "upload_id": uuid4(),
        "indicator_month": date(2023, 3, 1),
        "inflation_rate": Decimal("25.4"),
        "unemployment_rate": Decimal("4.7"),
        "cpi_index": Decimal("108.2"),
    }
    values.update(changes)
    return Module1EconomicContext(**values)


def real_eesi() -> Module2EESIResult:
    return Module2EESIResult(
        employee_id="PILOT-0002",
        eesi_score=52.5,
        economic_pressure_level="Unavailable",
        score_scale="0-100",
        formula_identifier="additive",
        formula_version="pp1-exploratory-v1",
        reference_profile="pilot",
    )


def test_real_module2_maps_module1_fields_and_preserves_scale_and_provenance(monkeypatch):
    captured = {}

    def fake_calculate(**values):
        captured.update(values)
        return {"scores": {"additive": 63.25}, "version": "verified-version"}

    monkeypatch.setattr("app.module4.providers.real_module2_provider.calculate", fake_calculate)
    result = RealModule2Provider(
        formula_identifier="additive", reference_profile="pilot"
    ).get_eesi_result(employee(), economic())

    assert captured["salary"] == 75000
    assert captured["inflation"] == 25.4
    assert captured["cpi"] == 108.2
    assert captured["unemployment"] == 4.7
    assert result.eesi_score == 63.25
    assert result.score_scale == "0-100"
    assert result.formula_identifier == "additive"
    assert result.formula_version == "verified-version"
    assert result.economic_pressure_level == "Unavailable"


@pytest.mark.parametrize(
    ("person", "context", "message"),
    [
        (employee(salary=None), economic(), "salary is missing"),
        (employee(), None, "no mapped economic context"),
        (employee(), economic(cpi_index=None), "cpi_index is missing"),
    ],
)
def test_real_module2_rejects_missing_required_context(person, context, message):
    provider = RealModule2Provider(formula_identifier="additive")
    with pytest.raises(ProviderResultUnavailableError, match=message):
        provider.get_eesi_result(person, context)


def test_real_module2_requires_explicit_formula_selection():
    with pytest.raises(ProviderResultUnavailableError, match="no EESI formula"):
        RealModule2Provider(formula_identifier=None).get_eesi_result(employee(), economic())


def test_real_module3_maps_exact_features_and_overtime_values():
    yes_record = RealModule3Provider.build_feature_record(employee(overtime=True), real_eesi())
    no_record = RealModule3Provider.build_feature_record(employee(overtime=False), real_eesi())

    assert list(yes_record) == [
        "Age", "MonthlyIncome", "OverTime", "JobSatisfaction", "JobLevel",
        "YearsAtCompany", "Department", "EESI",
    ]
    assert yes_record["OverTime"] == "Yes"
    assert no_record["OverTime"] == "No"
    assert yes_record["EESI"] == 52.5


def test_real_module3_extracts_only_explicit_positive_class():
    prediction = {"class_probabilities": {"No": 0.27, "Yes": 0.73}}
    assert RealModule3Provider.extract_positive_probability(prediction, "Yes") == 0.73
    with pytest.raises(ProviderResultUnavailableError, match="verified positive class"):
        RealModule3Provider.extract_positive_probability(prediction, "Leave")


def test_real_module3_reports_missing_model_artifact(monkeypatch):
    monkeypatch.setattr(
        "app.module4.providers.real_module3_provider.get_model_status",
        lambda: {"model_available": False, "message": "artifact missing"},
    )
    provider = RealModule3Provider(positive_class_label="Yes")
    with pytest.raises(ProviderResultUnavailableError, match="artifact missing"):
        provider.get_prediction(employee(), real_eesi())


def test_real_module3_does_not_invent_risk_or_explanation_contracts(monkeypatch):
    monkeypatch.setattr(
        "app.module4.providers.real_module3_provider.get_model_status",
        lambda: {
            "model_available": True,
            "classes": ["No", "Yes"],
            "feature_columns": [
                "Age", "MonthlyIncome", "OverTime", "JobSatisfaction", "JobLevel",
                "YearsAtCompany", "Department", "EESI",
            ],
            "eesi_integration": {
                "enabled": True,
                "formula_id": "additive",
                "formula_version": "pp1-exploratory-v1",
            },
        },
    )
    provider = RealModule3Provider(positive_class_label="Yes")
    with pytest.raises(ProviderResultUnavailableError, match="risk classification and feature explanation"):
        provider.get_prediction(employee(), real_eesi())


def test_mock_provider_contract_remains_backward_compatible():
    person = employee()
    eesi = MockModule2Provider().get_eesi_result(person, None)
    prediction = MockModule3Provider().get_prediction(person, eesi)

    assert eesi.employee_id == person.employee_id
    assert prediction.employee_id == person.employee_id
    assert prediction.risk_level == "High"


def test_provider_selection_defaults_to_mock_and_real_does_not_fallback():
    defaults = Settings()
    assert isinstance(build_module2_provider(defaults), MockModule2Provider)
    assert isinstance(build_module3_provider(defaults), MockModule3Provider)

    configured = Settings(
        module2_provider="real",
        module3_provider="real",
        module2_eesi_formula=None,
        module3_positive_class_label=None,
    )
    module2 = build_module2_provider(configured)
    module3 = build_module3_provider(configured)
    assert isinstance(module2, RealModule2Provider)
    assert isinstance(module3, RealModule3Provider)
    assert module2.metadata.source == "module2"
    assert module3.metadata.source == "module3"
    with pytest.raises(ProviderResultUnavailableError, match="no EESI formula"):
        module2.get_eesi_result(employee(), economic())
    with pytest.raises(ProviderResultUnavailableError, match="positive attrition class"):
        module3.get_prediction(employee(), real_eesi())
