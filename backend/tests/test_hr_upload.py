import csv
from io import StringIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app


class FakeResponse:
    def __init__(self, data):
        self.data = data


class FakeTable:
    def __init__(self, name: str, calls: list[tuple[str, object]]):
        self.name = name
        self.calls = calls
        self.payload = None

    def insert(self, payload):
        self.payload = payload
        self.calls.append((self.name, payload))
        return self

    def execute(self):
        return FakeResponse([{"id": "upload-test-id"}] if self.name == "dataset_uploads" else [])


class FakeSupabaseClient:
    def __init__(self):
        self.calls: list[tuple[str, object]] = []

    def table(self, name: str):
        return FakeTable(name, self.calls)


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr("app.routers.hr.find_existing_upload", lambda *args: None)
    fake_client = FakeSupabaseClient()
    monkeypatch.setattr("app.routers.hr.get_supabase_client", lambda: fake_client)
    return TestClient(app), fake_client


def sample_csv(rows=None, columns=None) -> bytes:
    columns = columns or [
        "EmployeeID", "Age", "Gender", "Department", "JobRole", "JobLevel",
        "MonthlyIncome", "BusinessTravel", "DistanceFromHome", "EducationField",
        "MaritalStatus", "OverTime", "JobSatisfaction", "EnvironmentSatisfaction",
        "WorkLifeBalance", "TotalWorkingYears", "YearsAtCompany", "JoinDate",
        "ResignationDate", "ObservationDate", "Attrition",
    ]
    rows = rows or [{
        "EmployeeID": "EMP001", "Age": "32", "Gender": "Female", "Department": "Sales",
        "JobRole": "Sales Executive", "JobLevel": "2", "MonthlyIncome": "50000",
        "BusinessTravel": "Travel_Rarely", "DistanceFromHome": "8", "EducationField": "Marketing",
        "MaritalStatus": "Single", "OverTime": "No", "JobSatisfaction": "3",
        "EnvironmentSatisfaction": "3", "WorkLifeBalance": "3", "TotalWorkingYears": "8",
        "YearsAtCompany": "4", "JoinDate": "2019-01-01", "ResignationDate": "",
        "ObservationDate": "2023-03-15", "Attrition": "No",
    }]
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode()


def post_csv(client: TestClient, content: bytes, filename="hr.csv"):
    return client.post("/api/v1/hr/upload", files={"file": (filename, content, "text/csv")})


def test_valid_pilot_hr_csv_is_stored(client):
    test_client, fake_supabase = client
    pilot_path = Path(__file__).parents[2] / "pilot-data" / "module1_hr_pilot_100_employees.csv"

    response = post_csv(test_client, pilot_path.read_bytes(), pilot_path.name)

    assert response.status_code == 201
    assert response.json()["total_records"] == 100
    assert response.json()["valid_records"] == 100
    assert response.json()["observation_period"] == {"start": "2023-01", "end": "2023-06"}
    assert [name for name, _ in fake_supabase.calls] == ["dataset_uploads", "employee_records", "validation_reports"]


def test_missing_observation_date_column_is_rejected(client):
    test_client, _ = client
    columns = [column for column in sample_csv().decode().splitlines()[0].split(",") if column != "ObservationDate"]

    response = post_csv(test_client, sample_csv(columns=columns))

    assert response.status_code == 422
    assert "ObservationDate" in response.json()["errors"][0]["columns"]


def test_invalid_observation_date_is_rejected(client):
    test_client, _ = client
    content = sample_csv(rows=[{**_sample_row(), "ObservationDate": "not-a-date"}])

    response = post_csv(test_client, content)

    assert response.status_code == 422
    assert any(error["field"] == "ObservationDate" for error in response.json()["errors"])


def test_observation_date_outside_pilot_period_is_rejected(client):
    test_client, _ = client
    content = sample_csv(rows=[{**_sample_row(), "ObservationDate": "2023-07-01"}])

    response = post_csv(test_client, content)

    assert response.status_code == 422
    assert any("2023-01-01" in error["message"] for error in response.json()["errors"])


def test_duplicate_employee_id_is_rejected(client):
    test_client, _ = client
    content = sample_csv(rows=[_sample_row(), {**_sample_row(), "ObservationDate": "2023-04-15"}])

    response = post_csv(test_client, content)

    assert response.status_code == 422
    assert response.json()["duplicate_employee_ids"] == 1


def test_missing_required_column_is_rejected(client):
    test_client, _ = client
    columns = [column for column in sample_csv().decode().splitlines()[0].split(",") if column != "MonthlyIncome"]

    response = post_csv(test_client, sample_csv(columns=columns))

    assert response.status_code == 422
    assert "MonthlyIncome" in response.json()["errors"][0]["columns"]


def test_empty_csv_is_rejected(client):
    test_client, _ = client

    response = post_csv(test_client, b"")

    assert response.status_code == 422
    assert response.json()["errors"][0]["message"] == "CSV file is empty"


def _sample_row():
    return {
        "EmployeeID": "EMP001", "Age": "32", "Gender": "Female", "Department": "Sales",
        "JobRole": "Sales Executive", "JobLevel": "2", "MonthlyIncome": "50000",
        "BusinessTravel": "Travel_Rarely", "DistanceFromHome": "8", "EducationField": "Marketing",
        "MaritalStatus": "Single", "OverTime": "No", "JobSatisfaction": "3",
        "EnvironmentSatisfaction": "3", "WorkLifeBalance": "3", "TotalWorkingYears": "8",
        "YearsAtCompany": "4", "JoinDate": "2019-01-01", "ResignationDate": "",
        "ObservationDate": "2023-03-15", "Attrition": "No",
    }


def test_duplicate_upload_reuses_existing_dataset(client, monkeypatch):
    test_client, fake = client
    monkeypatch.setattr('app.routers.hr.find_existing_upload', lambda *args: 'existing-hr')
    response = post_csv(test_client, sample_csv(), 'renamed.csv')
    assert response.status_code == 200
    assert response.json()['duplicate_upload'] is True
    assert response.json()['upload_id'] == 'existing-hr'
    assert fake.calls == []


def test_expanded_pilot_has_300_unique_ids_and_preserves_original():
    from app.services.hr_upload import validate_hr_csv
    root = Path(__file__).parents[2] / 'pilot-data'
    original = list(csv.DictReader((root / 'module1_hr_pilot_100_employees.csv').open(encoding='utf-8-sig', newline='')))
    path = root / 'module1_hr_pilot_300_employees.csv'
    expanded = list(csv.DictReader(path.open(encoding='utf-8-sig', newline='')))
    assert expanded[:100] == original
    assert len({row['EmployeeID'] for row in expanded}) == 300
    result = validate_hr_csv(path.read_bytes(), path.name)
    assert result.is_valid
    assert result.summary['total_records'] == 300
