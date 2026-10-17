import csv
from io import StringIO

from fastapi.testclient import TestClient

from app.main import app
from app.services.module3_export import EXPORT_COLUMNS, FEATURE_COLUMNS, build_pilot_export


def test_module3_contract_describes_explicit_eesi_boundary():
    client = TestClient(app)
    response = client.get("/api/v1/module3/integration-contract")

    assert response.status_code == 200
    body = response.json()
    assert body["dataset_kind"] == "synthetic_pilot_only"
    assert body["eesi"]["column"] == "EESI"
    assert body["eesi"]["formula_version_column"] == "EESIFormulaVersion"
    assert body["feature_columns"] == FEATURE_COLUMNS


def test_pilot_export_contains_one_selected_eesi_version_and_no_extra_columns():
    client = TestClient(app)
    response = client.get("/api/v1/module3/pilot-export?formula_id=additive")

    assert response.status_code == 200
    assert response.headers["x-dataset-provenance"] == "synthetic-pilot-only-not-research-evidence"
    rows = list(csv.DictReader(StringIO(response.text)))
    assert len(rows) == 100
    assert list(rows[0]) == EXPORT_COLUMNS
    assert {row["EESIFormulaId"] for row in rows} == {"additive"}
    assert len({row["EESIFormulaVersion"] for row in rows}) == 1
    assert "ResignationDate" not in rows[0]


def test_pilot_export_rejects_unknown_formula():
    client = TestClient(app)
    response = client.get("/api/v1/module3/pilot-export?formula_id=unknown")

    assert response.status_code == 422
    assert "Unsupported formula_id" in response.json()["detail"]


def test_service_export_matches_requested_formula():
    rows = build_pilot_export("economic")

    assert all(row["EESIFormulaId"] == "economic" for row in rows)
    assert all(0 <= row["EESI"] <= 100 for row in rows)


def test_prediction_status_and_endpoints_expose_safe_model_contract(monkeypatch):
    client = TestClient(app)
    status_payload = {
        "model_available": True,
        "dataset_kind": "synthetic_pilot_only",
        "feature_columns": ["Age", "EESI"],
        "classes": ["No", "Yes"],
    }
    prediction_payload = {"predicted_class": "No", "class_probabilities": {"No": 0.8, "Yes": 0.2}}
    evaluation_payload = {"metrics": {"accuracy": 0.5}, "confusion_matrix": [[1, 0], [1, 0]]}
    monkeypatch.setattr("app.routers.module3.get_model_status", lambda: status_payload)
    monkeypatch.setattr("app.routers.module3.predict_saved_model", lambda record: prediction_payload)
    monkeypatch.setattr("app.routers.module3.load_evaluation_report", lambda: evaluation_payload)

    assert client.get("/api/v1/module3/prediction-status").json() == status_payload
    assert client.post("/api/v1/module3/predict", json={"record": {"Age": 30, "EESI": 42.0}}).json() == prediction_payload
    assert client.get("/api/v1/module3/evaluation").json() == evaluation_payload
