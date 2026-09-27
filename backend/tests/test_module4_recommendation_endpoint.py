from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.module4.providers.base import ProviderMetadata, ProviderResultUnavailableError
from app.module4.providers.mock_module2_provider import MockModule2Provider
from app.module4.providers.mock_module3_provider import MockModule3Provider
from app.module4.repositories.employee_repository import EmployeeNotFoundError
from app.module4.routers.recommendations import get_decision_service
from app.module4.schemas.integration import (
    Module1EmployeeContext,
    Module2EESIResult,
    Module3PredictionResult,
)
from app.module4.services.decision_service import RetentionDecisionService


def employee(employee_id: str = "EMP002") -> Module1EmployeeContext:
    return Module1EmployeeContext(
        id=uuid4(), upload_id=uuid4(), employee_id=employee_id,
        overtime=True, job_satisfaction=2, work_life_balance=2,
        attrition=False, created_at=datetime.now(timezone.utc),
    )


class FakeEmployeeRepository:
    def __init__(self, person: Module1EmployeeContext | None = None) -> None:
        self.person = person

    def get_employee_context(self, employee_id: str) -> Module1EmployeeContext:
        if self.person is None:
            raise EmployeeNotFoundError(f"Employee ID '{employee_id}' was not found")
        return self.person

    def get_employee_economic_context(self, employee_record_id):
        return None


class UnavailableModule2Provider:
    metadata = ProviderMetadata("mock", "mock_integration", True)

    def get_eesi_result(self, employee, economic_context):
        raise ProviderResultUnavailableError("Module 2 result is unavailable")


class UnavailableModule3Provider:
    metadata = ProviderMetadata("mock", "mock_integration", True)

    def get_prediction(self, employee):
        raise ProviderResultUnavailableError("Module 3 result is unavailable")


class MismatchingModule3Provider:
    metadata = ProviderMetadata("mock", "mock_integration", True)

    def get_prediction(self, employee):
        return Module3PredictionResult(
            employee_id="DIFFERENT", turnover_probability=0.8, risk_level="High",
        )


@pytest.fixture(autouse=True)
def clear_dependency_override():
    yield
    app.dependency_overrides.pop(get_decision_service, None)


def client_for(service: RetentionDecisionService) -> TestClient:
    app.dependency_overrides[get_decision_service] = lambda: service
    return TestClient(app)


def test_recommendation_endpoint_returns_mock_metadata_and_ranked_output() -> None:
    service = RetentionDecisionService(
        FakeEmployeeRepository(employee()),  # type: ignore[arg-type]
        MockModule2Provider(),
        MockModule3Provider(),
    )

    response = client_for(service).get("/api/v1/module4/employees/EMP002/recommendations")

    assert response.status_code == 200
    body = response.json()
    assert body["employee_id"] == "EMP002"
    assert body["risk_level"] == "High"
    assert body["economic_pressure_level"] == "High"
    assert body["metadata"]["data_mode"] == "mock_integration"
    assert body["metadata"]["module2_source"] == "mock"
    assert body["metadata"]["module3_source"] == "mock"
    assert "not calculated EESI" in body["metadata"]["disclaimer"]
    assert body["recommendations"][0]["priority_score"] >= body["recommendations"][-1]["priority_score"]


def test_unknown_employee_returns_404() -> None:
    service = RetentionDecisionService(
        FakeEmployeeRepository(),  # type: ignore[arg-type]
        MockModule2Provider(),
        MockModule3Provider(),
    )

    response = client_for(service).get("/api/v1/module4/employees/UNKNOWN/recommendations")

    assert response.status_code == 404


def test_unavailable_module2_result_returns_503() -> None:
    service = RetentionDecisionService(
        FakeEmployeeRepository(employee()),  # type: ignore[arg-type]
        UnavailableModule2Provider(),  # type: ignore[arg-type]
        MockModule3Provider(),
    )

    response = client_for(service).get("/api/v1/module4/employees/EMP002/recommendations")

    assert response.status_code == 503
    assert "Module 2" in response.json()["detail"]


def test_unavailable_module3_result_returns_503() -> None:
    service = RetentionDecisionService(
        FakeEmployeeRepository(employee()),  # type: ignore[arg-type]
        MockModule2Provider(),
        UnavailableModule3Provider(),  # type: ignore[arg-type]
    )

    response = client_for(service).get("/api/v1/module4/employees/EMP002/recommendations")

    assert response.status_code == 503
    assert "Module 3" in response.json()["detail"]


def test_mismatching_provider_employee_id_returns_502() -> None:
    service = RetentionDecisionService(
        FakeEmployeeRepository(employee()),  # type: ignore[arg-type]
        MockModule2Provider(),
        MismatchingModule3Provider(),  # type: ignore[arg-type]
    )

    response = client_for(service).get("/api/v1/module4/employees/EMP002/recommendations")

    assert response.status_code == 502
    assert "did not match" in response.json()["detail"]
