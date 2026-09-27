from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.module4.repositories.employee_repository import (
    AmbiguousEmployeeError,
    EmployeeNotFoundError,
    EmployeeRepository,
)


class FakeResponse:
    def __init__(self, data: list[dict[str, object]]) -> None:
        self.data = data


class FakeQuery:
    def __init__(self, data: list[dict[str, object]]) -> None:
        self.data = data
        self.filters: list[tuple[str, object]] = []
        self.selected = ""

    def select(self, columns: str) -> "FakeQuery":
        self.selected = columns
        return self

    def eq(self, column: str, value: object) -> "FakeQuery":
        self.filters.append((column, value))
        return self

    def order(self, column: str, *, desc: bool = False) -> "FakeQuery":
        return self

    def limit(self, count: int) -> "FakeQuery":
        return self

    def execute(self) -> FakeResponse:
        return FakeResponse(self.data)


class FakeSupabaseClient:
    def __init__(self, table_data: dict[str, list[dict[str, object]]]) -> None:
        self.table_data = table_data
        self.queries: list[tuple[str, FakeQuery]] = []

    def table(self, name: str) -> FakeQuery:
        query = FakeQuery(self.table_data.get(name, []))
        self.queries.append((name, query))
        return query


def employee_row() -> dict[str, object]:
    return {
        "id": str(uuid4()),
        "upload_id": str(uuid4()),
        "employee_id": "EMP001",
        "age": 31,
        "gender": "Female",
        "salary": "75000.00",
        "department": "Research",
        "job_role": "Analyst",
        "job_level": 2,
        "business_travel": "Travel_Rarely",
        "distance_from_home": 5,
        "education_field": "Science",
        "marital_status": "Single",
        "overtime": False,
        "job_satisfaction": 3,
        "environment_satisfaction": 4,
        "work_life_balance": 3,
        "total_working_years": 8,
        "years_at_company": 3,
        "join_date": "2020-01-10",
        "resignation_date": None,
        "observation_date": "2023-03-15",
        "attrition": False,
        "raw_data": {},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def test_repository_looks_up_external_employee_identifier() -> None:
    fake = FakeSupabaseClient({"employee_records": [employee_row()]})
    repository = EmployeeRepository(client=fake)  # type: ignore[arg-type]

    employee = repository.get_employee_by_employee_id("  EMP001  ")

    assert employee is not None
    assert employee.employee_id == "EMP001"
    assert fake.queries[0][0] == "employee_records"
    assert ("employee_id", "EMP001") in fake.queries[0][1].filters


def test_repository_returns_none_for_missing_employee() -> None:
    repository = EmployeeRepository(client=FakeSupabaseClient({}))  # type: ignore[arg-type]

    assert repository.get_employee_by_employee_id("EMP404") is None


def test_required_context_raises_for_missing_employee() -> None:
    repository = EmployeeRepository(client=FakeSupabaseClient({}))  # type: ignore[arg-type]

    with pytest.raises(EmployeeNotFoundError, match="EMP404"):
        repository.get_employee_context("EMP404")


def test_blank_employee_identifier_is_rejected_before_query() -> None:
    fake = FakeSupabaseClient({})
    repository = EmployeeRepository(client=fake)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="non-empty"):
        repository.get_employee_by_employee_id("  ")
    assert fake.queries == []


def test_duplicate_external_id_requires_upload_id() -> None:
    row = employee_row()
    repository = EmployeeRepository(
        client=FakeSupabaseClient({"employee_records": [row, {**row, "upload_id": str(uuid4())}]})  # type: ignore[arg-type]
    )

    with pytest.raises(AmbiguousEmployeeError, match="provide upload_id"):
        repository.get_employee_by_employee_id("EMP001")


def test_economic_context_uses_temporal_mapping_not_integrated_records() -> None:
    economic_id = uuid4()
    upload_id = uuid4()
    fake = FakeSupabaseClient({
        "temporal_mappings": [{
            "economic_indicators": {
                "id": str(economic_id),
                "upload_id": str(upload_id),
                "indicator_month": "2023-03-01",
                "inflation_rate": "50.3",
                "unemployment_rate": "4.8",
                "cost_of_living_index": "108.59",
                "cpi_index": "108.59",
                "policy_interest_rate_percent": "16.5",
                "usd_lkr_exchange_rate": "355.0",
                "gdp_growth_rate_percent": "-10.0",
            }
        }]
    })
    repository = EmployeeRepository(client=fake)  # type: ignore[arg-type]

    context = repository.get_employee_economic_context(uuid4())

    assert context is not None
    assert context.id == economic_id
    assert fake.queries[0][0] == "temporal_mappings"
    assert all(table != "integrated_records" for table, _ in fake.queries)
