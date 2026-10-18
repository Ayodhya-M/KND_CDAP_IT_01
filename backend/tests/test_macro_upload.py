import csv
from io import StringIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app


class FakeResponse:
    def __init__(self, data): self.data = data


class FakeTable:
    def __init__(self, name, calls): self.name, self.calls = name, calls
    def insert(self, payload): self.calls.append((self.name, payload)); return self
    def execute(self): return FakeResponse([{"id": "macro-upload-id"}] if self.name == "dataset_uploads" else [])


class FakeSupabaseClient:
    def __init__(self): self.calls = []
    def table(self, name): return FakeTable(name, self.calls)


@pytest.fixture
def client(monkeypatch):
    fake = FakeSupabaseClient()
    monkeypatch.setattr("app.routers.macro.get_supabase_client", lambda: fake)
    return TestClient(app), fake


def sample_row():
    return {"Date": "2023-03-01", "Year": "2023", "Month": "3", "Inflation_Rate_Percent": "50.3", "CPI_Index": "108.59", "Unemployment_Rate_Percent": "4.8", "Policy_Interest_Rate_Percent": "16.5", "USD_LKR_Exchange_Rate": "355", "GDP_Growth_Rate_Percent": "-10.0"}


def sample_csv(rows=None, columns=None):
    columns = columns or list(sample_row())
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore")
    writer.writeheader(); writer.writerows(rows or [sample_row()])
    return output.getvalue().encode()


def post_csv(client, content, filename="macro.csv"):
    return client.post("/api/v1/macroeconomic/upload", files={"file": (filename, content, "text/csv")})


def test_valid_pilot_macro_csv_is_stored(client):
    test_client, fake = client
    path = Path(__file__).parents[2] / "pilot-data" / "module1_sri_lanka_macro_pilot_6_months.csv"
    response = post_csv(test_client, path.read_bytes(), path.name)
    assert response.status_code == 201
    assert response.json()["total_records"] == 6
    assert response.json()["economic_period"] == {"start": "2023-01", "end": "2023-06"}
    assert [name for name, _ in fake.calls] == ["dataset_uploads", "economic_indicators", "validation_reports"]


def test_missing_required_column_is_rejected(client):
    test_client, _ = client
    response = post_csv(test_client, sample_csv(columns=[column for column in sample_row() if column != "CPI_Index"]))
    assert response.status_code == 422
    assert "CPI_Index" in response.json()["errors"][0]["columns"]


def test_invalid_monthly_date_is_rejected(client):
    test_client, _ = client
    response = post_csv(test_client, sample_csv([{**sample_row(), "Date": "2023-03-15"}]))
    assert response.status_code == 422
    assert any("first day" in error["message"] for error in response.json()["errors"])


def test_duplicate_month_is_rejected(client):
    test_client, _ = client
    response = post_csv(test_client, sample_csv([sample_row(), sample_row()]))
    assert response.status_code == 422
    assert response.json()["duplicate_months"] == 1


def test_invalid_numeric_value_is_rejected(client):
    test_client, _ = client
    response = post_csv(test_client, sample_csv([{**sample_row(), "CPI_Index": "unknown"}]))
    assert response.status_code == 422
    assert any(error["field"] == "CPI_Index" for error in response.json()["errors"])


def test_empty_csv_is_rejected(client):
    test_client, _ = client
    response = post_csv(test_client, b"")
    assert response.status_code == 422
