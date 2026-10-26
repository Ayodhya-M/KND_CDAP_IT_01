from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.system_actor import require_research_system_actor

UPLOAD_ID = "2f9fb572-6c80-4465-909b-fea9f8878d0a"


class Response:
    def __init__(self, data=None): self.data = data or []


class Query:
    def __init__(self, client, table): self.client, self.table, self.operation, self.payload = client, table, "select", None
    def select(self, columns): return self
    def eq(self, column, value): return self
    def limit(self, count): return self
    def insert(self, payload): self.operation, self.payload = "insert", payload; return self
    def execute(self):
        if self.operation == "insert":
            self.client.inserts.append((self.table, self.payload))
            return Response([{"id": str(uuid4())}])
        return Response(self.client.tables.get(self.table, []))


class FakeClient:
    def __init__(self, rows=None):
        self.tables = {
            "profiles": [],
            "dataset_uploads": [{"id": UPLOAD_ID, "dataset_type": "hr", "original_filename": "pilot.csv", "file_format": "csv", "record_count": len(rows or [])}],
            "employee_records": rows or [],
        }
        self.inserts = []
    def table(self, name): return Query(self, name)


def complete_row():
    fields = (
        "employee_id", "age", "salary", "department", "join_date", "observation_date", "attrition", "gender",
        "job_role", "job_level", "business_travel", "distance_from_home", "education_field", "marital_status",
        "overtime", "job_satisfaction", "environment_satisfaction", "work_life_balance", "total_working_years", "years_at_company",
    )
    return {field: "value" for field in fields}


@pytest.fixture(autouse=True)
def clear_override():
    yield
    app.dependency_overrides.pop(require_research_system_actor, None)


def test_missing_system_actor_configuration_disables_operation(monkeypatch):
    monkeypatch.setattr("app.system_actor.get_settings", lambda: SimpleNamespace(research_system_actor_id=None))
    with pytest.raises(HTTPException) as caught: require_research_system_actor()
    assert caught.value.status_code == 503


def test_configured_actor_must_reference_existing_profile(monkeypatch):
    actor_id, client = uuid4(), FakeClient()
    monkeypatch.setattr("app.system_actor.get_settings", lambda: SimpleNamespace(research_system_actor_id=actor_id))
    monkeypatch.setattr("app.system_actor.get_supabase_client", lambda: client)
    with pytest.raises(HTTPException) as caught: require_research_system_actor()
    assert caught.value.status_code == 503


def test_configured_existing_actor_is_returned(monkeypatch):
    actor_id, client = uuid4(), FakeClient()
    client.tables["profiles"] = [{"id": str(actor_id), "role": "researcher"}]
    monkeypatch.setattr("app.system_actor.get_settings", lambda: SimpleNamespace(research_system_actor_id=actor_id))
    monkeypatch.setattr("app.system_actor.get_supabase_client", lambda: client)
    assert require_research_system_actor() == actor_id


def test_authorized_analysis_records_configured_actor(monkeypatch):
    client, actor_id = FakeClient([complete_row()]), uuid4()
    app.dependency_overrides[require_research_system_actor] = lambda: actor_id
    monkeypatch.setattr("app.routers.data_cleaning.get_supabase_client", lambda: client)
    response = TestClient(app).get(f"/api/v1/data-cleaning/analyse/{UPLOAD_ID}")
    assert response.status_code == 200
    audit = next(payload for table, payload in client.inserts if table == "data_cleaning_runs")
    assert audit["initiated_by"] == str(actor_id)


def test_missing_dataset_returns_404(monkeypatch):
    client = FakeClient(); client.tables["dataset_uploads"] = []
    app.dependency_overrides[require_research_system_actor] = uuid4
    monkeypatch.setattr("app.routers.data_cleaning.get_supabase_client", lambda: client)
    assert TestClient(app).get(f"/api/v1/data-cleaning/analyse/{UPLOAD_ID}").status_code == 404


def test_remove_missing_stops_before_any_write_without_transaction(monkeypatch):
    client = FakeClient([{"employee_id": "EMP001", "salary": None}])
    app.dependency_overrides[require_research_system_actor] = uuid4
    monkeypatch.setattr("app.routers.data_cleaning.get_supabase_client", lambda: client)
    response = TestClient(app).post("/api/v1/data-cleaning/remove-missing", json={"upload_id": UPLOAD_ID})
    assert response.status_code == 503
    assert "no records were changed" in response.json()["detail"]
    assert client.inserts == []


def test_no_missing_rows_records_safe_noop_cleaning_run(monkeypatch):
    client, actor_id = FakeClient([complete_row()]), uuid4()
    app.dependency_overrides[require_research_system_actor] = lambda: actor_id
    monkeypatch.setattr("app.routers.data_cleaning.get_supabase_client", lambda: client)
    response = TestClient(app).post("/api/v1/data-cleaning/remove-missing", json={"upload_id": UPLOAD_ID})
    assert response.status_code == 201
    assert [table for table, _ in client.inserts] == ["data_cleaning_runs"]
