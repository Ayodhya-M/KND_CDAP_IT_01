import math

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.eesi import calculate, pilot_preview


def test_hand_worked_midpoint_and_contributions():
    result = calculate(50000, 32.6, 107.635, 4.7)
    assert result["scores"] == pytest.approx({"economic": 50, "additive": 50, "interaction": 25})
    for formula, contributions in result["contributions"].items():
        assert sum(contributions.values()) == pytest.approx(result["scores"][formula])


def test_salary_changes_only_employee_candidates():
    low = calculate(25000, 40, 110, 4.7)
    high = calculate(100000, 40, 110, 4.7)
    assert low["scores"]["economic"] == high["scores"]["economic"]
    for formula in ["additive", "interaction"]:
        assert low["scores"][formula] > high["scores"][formula]


def test_component_increase_and_frozen_reference():
    original = calculate(50000, 25, 105, 4.7)
    changed = calculate(50000, 35, 105, 4.7)
    for formula in original["scores"]:
        assert changed["scores"][formula] > original["scores"][formula]
    pilot_preview()
    assert calculate(50000, 25, 105, 4.7) == original


def test_clipping_is_bounded_and_reported():
    result = calculate(1, 1000, 1000, 100)
    assert len(result["warnings"]) == 3
    assert all(0 <= value <= 100 for value in result["scores"].values())


def test_extreme_finite_income_does_not_overflow():
    result = calculate(1e308, 32.6, 107.635, 4.7, reference_salary=1e308)
    assert result["components"]["salary_exposure"] == 0.5


def test_reference_endpoints_are_not_absolute_stress_labels():
    lower = calculate(50000, 12, 100, 4.6)
    upper = calculate(50000, 53.2, 115.27, 4.8)
    assert lower["scores"] == pytest.approx({"economic": 0, "additive": 12.5, "interaction": 0})
    assert upper["scores"] == pytest.approx({"economic": 100, "additive": 87.5, "interaction": 50})


@pytest.mark.parametrize("salary", [0, -1, math.nan, math.inf])
def test_invalid_salary_rejected(salary):
    with pytest.raises(ValueError):
        calculate(salary, 25, 105, 4.7)


def test_pilot_covers_all_employees_without_outcome_inputs():
    result = pilot_preview()
    assert len(result["rows"]) == 100
    assert not result["rejected"]
    assert len(result["months"]) == 6
    assert all("attrition" not in row["inputs"] for row in result["rows"])


def test_both_pilot_views_keep_original_scores_without_inventing_finances():
    small = pilot_preview()
    large = pilot_preview(300)
    assert len(large['rows']) == 300
    assert not large['rejected']
    assert small == pilot_preview(100)
    for row in small['rows'] + large['rows']:
        assert set(row['scores']) == {'economic', 'additive', 'interaction'}
        assert 'financial_burden' not in row['components']
        inputs = row['inputs']
        assert calculate(**inputs)['scores'] == row['scores']
    client = TestClient(app)
    assert len(client.get('/api/v1/eesi/pilot').json()['rows']) == 100
    assert len(client.get('/api/v1/eesi/pilot?size=300').json()['rows']) == 300
    assert client.get('/api/v1/eesi/pilot?size=200').status_code == 422


def test_api_works_without_supabase(monkeypatch):
    def forbidden():
        raise AssertionError("EESI must not access Supabase")
    monkeypatch.setattr("app.main.get_supabase_client", forbidden)
    client = TestClient(app)
    assert client.get("/api/v1/eesi/pilot").status_code == 200
    response = client.post("/api/v1/eesi/scenario", json={"salary": 50000, "inflation": 32.6, "cpi": 107.635, "unemployment": 4.7})
    assert response.status_code == 200
    assert response.json()["scores"]["interaction"] == pytest.approx(25)
    assert client.post("/api/v1/eesi/scenario", json={"salary": 0, "inflation": 25, "cpi": 105, "unemployment": 4.7}).status_code == 422
