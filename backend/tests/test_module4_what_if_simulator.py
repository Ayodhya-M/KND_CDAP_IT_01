from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.module4.providers.mock_module2_provider import MockModule2Provider
from app.module4.providers.mock_module3_provider import MockModule3Provider
from app.module4.routers.recommendations import get_decision_service
from app.module4.schemas.integration import Module1EmployeeContext
from app.module4.schemas.simulation import SIMULATION_LABEL, WhatIfChanges
from app.module4.services.decision_service import RetentionDecisionService
from app.module4.services.what_if_simulator import WhatIfSimulator


class ReadOnlyRepository:
    def __init__(self, employee_id: str = "EMP002") -> None:
        self.employee = Module1EmployeeContext(
            id=uuid4(), upload_id=uuid4(), employee_id=employee_id,
            salary=Decimal("120000"), overtime=True, job_satisfaction=1,
            work_life_balance=1, attrition=False, created_at=datetime.now(timezone.utc),
        )
        self.read_count = 0
        self.write_count = 0

    def get_employee_context(self, employee_id: str):
        self.read_count += 1
        return self.employee

    def get_employee_economic_context(self, employee_record_id):
        self.read_count += 1
        return None

    def insert(self, *args, **kwargs):
        self.write_count += 1
        raise AssertionError("simulation must not write")

    update = delete = insert


def build_simulator(employee_id: str = "EMP002") -> tuple[WhatIfSimulator, ReadOnlyRepository]:
    repository = ReadOnlyRepository(employee_id)
    service = RetentionDecisionService(
        repository, MockModule2Provider(), MockModule3Provider(),  # type: ignore[arg-type]
    )
    return WhatIfSimulator(service), repository


def test_high_scenario_removes_only_resolved_supported_factors_and_keeps_probability() -> None:
    simulator, repository = build_simulator()

    result = simulator.simulate("EMP002", WhatIfChanges(
        overtime=False, job_satisfaction=4, work_life_balance=4,
    ))

    assert result.label == SIMULATION_LABEL
    assert result.original_turnover_probability == result.simulated_turnover_probability == 0.82
    assert result.probability_difference == 0
    assert result.removed_risk_factors == ["overtime", "job_satisfaction", "work_life_balance"]
    assert len(result.original_recommendations) == 6
    assert result.simulated_recommendations == []
    assert repository.write_count == 0


def test_partial_change_recalculates_and_preserves_priority_order() -> None:
    simulator, _ = build_simulator()
    result = simulator.simulate("EMP002", WhatIfChanges(overtime=False))

    assert "overtime" in result.removed_risk_factors
    assert {item.related_factor for item in result.simulated_recommendations} == {
        "job_satisfaction", "work_life_balance",
    }
    scores = [item.priority_score for item in result.simulated_recommendations]
    assert scores == sorted(scores, reverse=True)


def test_salary_change_is_displayed_without_inventing_a_threshold_or_prediction() -> None:
    simulator, _ = build_simulator()
    result = simulator.simulate("EMP002", WhatIfChanges(salary=150000))

    assert result.simulated_values.salary == 150000
    assert result.original_recommendations == result.simulated_recommendations
    assert result.probability_difference == 0


@pytest.mark.parametrize("payload", [{}, {"salary": 0}, {"job_satisfaction": 5}, {"work_life_balance": 0}])
def test_invalid_scenario_values_are_rejected(payload) -> None:
    with pytest.raises(ValidationError):
        WhatIfChanges.model_validate(payload)


def test_low_scenario_remains_without_unnecessary_recommendations() -> None:
    simulator, _ = build_simulator("EMP003")
    result = simulator.simulate("EMP003", WhatIfChanges(overtime=False))
    assert result.original_recommendations == result.simulated_recommendations == []


def test_simulation_endpoint_is_compatible_and_explicitly_illustrative() -> None:
    simulator, _ = build_simulator()
    service = simulator.decision_service
    app.dependency_overrides[get_decision_service] = lambda: service
    try:
        response = TestClient(app).post(
            "/api/v1/module4/employees/EMP002/simulation",
            json={"overtime": False},
        )
    finally:
        app.dependency_overrides.pop(get_decision_service, None)

    assert response.status_code == 200
    body = response.json()
    assert body["label"] == SIMULATION_LABEL
    assert body["metadata"]["data_mode"] == "mock_integration"
    assert body["probability_difference"] == 0
