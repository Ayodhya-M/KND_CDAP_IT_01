import csv
import json

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.eesi import calculate
from app.services.eesi_real import REAL_BOUNDS, REAL_VERSION, build_real_summary, prepare_employee, prior_month, summarize


def employee(**changes):
    return {"YEAR": "2024", "MONTH": "1", "AGE": "30", "Q45": "1", "Q45_A_1": "50000", "AnnualFactor_25Percent": "2", **changes}


def test_income_month_rollover_and_quarter_alignment():
    assert prior_month("2024", "1") == "2023-12"
    assert prior_month("2024", "4") == "2024-03"
    result = prepare_employee(employee(), {"2023-12": {"inflation": 4.2, "cpi": 208.8, "unemployment": 4.3}})
    assert result["income_month"] == "2023-12"
    assert result["survey_month"] == "2024-01"


@pytest.mark.parametrize("changes", [{"Q45": "2"}, {"Q45_A_1": " "}, {"Q45_A_1": "0"}, {"Q45_A_1": "nan"}, {"AnnualFactor_25Percent": "0"}, {"AGE": "14"}, {"YEAR": "2023"}, {"MONTH": "1.5"}])
def test_ineligible_and_invalid_values_are_rejected(changes):
    with pytest.raises(ValueError):
        prepare_employee(employee(**changes), {"2023-12": {"inflation": 4.2, "cpi": 208.8, "unemployment": 4.3}})


def test_missing_economic_month_is_not_imputed():
    with pytest.raises(ValueError, match="missing_economic_month"):
        prepare_employee(employee(), {})


def test_weighting_and_small_group_suppression():
    assert summarize([{"salary": 1}], "small")["scores"] is None
    rows = [{"weight": 1, "scores": dict.fromkeys(["economic", "additive", "interaction"], 10)}] * 15
    rows += [{"weight": 3, "scores": dict.fromkeys(["economic", "additive", "interaction"], 30)}] * 15
    group = summarize(rows, "test")
    assert group["scores"]["additive"] == {"sample_mean": 20, "weighted_mean": 25}


def test_real_scale_is_separate_and_allows_deflation():
    result = calculate(50000, -1.7, 202.1, 4.2, bounds=REAL_BOUNDS, version=REAL_VERSION)
    assert result["scores"] == pytest.approx({"economic": 0, "additive": 12.5, "interaction": 0})
    assert not result["warnings"]
    assert result["version"] == REAL_VERSION


def test_reference_ranges_cannot_be_constant():
    with pytest.raises(ValueError, match="nonconstant"):
        calculate(50000, 1, 200, 4, bounds={"inflation": (0, 0), "cpi": (100, 200), "unemployment": (0, 10)})


def test_preparation_uses_fixture_without_real_microdata(tmp_path):
    source = tmp_path / "source.csv"
    rows = [employee()] * 30 + [employee(Q45_A_1="0")]
    with source.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    summary = build_real_summary(source)
    assert summary["eligible_records"] == 30
    assert summary["excluded_records"] == 1
    assert summary["source_records"] == summary["eligible_records"] + sum(summary["exclusions"].values())
    assert "rows" not in summary
    assert "salary" not in json.dumps(summary["overall"])


def test_aggregate_endpoint_and_reference_profile(monkeypatch):
    monkeypatch.setattr("app.routers.eesi.load_real_summary", lambda: {"eligible_records": 30, "overall": {"count": 30}})
    client = TestClient(app)
    assert client.get("/api/v1/eesi/real-data").json()["eligible_records"] == 30
    response = client.post("/api/v1/eesi/scenario", json={"salary": 50000, "inflation": -1.7, "cpi": 202.1, "unemployment": 4.2, "reference_profile": "lfs2024"})
    assert response.status_code == 200
    assert response.json()["version"] == REAL_VERSION
    response = client.post("/api/v1/eesi/scenario", json={"salary": 50000, "inflation": 1, "cpi": 202.1, "unemployment": 4.2, "reference_profile": "unknown"})
    assert response.status_code == 422
