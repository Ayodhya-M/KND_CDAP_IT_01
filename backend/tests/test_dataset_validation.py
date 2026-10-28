from app.main import app
from app.services.dataset_validation import validate_integrated_dataset


def test_dataset_validation_router_is_registered():
    routes = {(route.path, tuple(route.methods or [])) for route in app.routes}
    assert ("/api/v1/dataset-validation/integration-runs", ("GET",)) in routes
    assert ("/api/v1/dataset-validation/integration/{integration_run_id}", ("GET",)) in routes


def _valid_record() -> dict:
    return {
        "employee_record_id": "employee-1", "employee_id": "EMP001", "age": 31,
        "salary": 120000, "additional_income": 10000, "overtime": True,
        "tenure_years": 4, "observation_date": "2023-03-17", "mapped_month": "2023-03-01",
        "inflation_rate": 50.3, "cpi_index": 108.59, "cost_of_living_index": 108.59,
        "unemployment_rate": 4.8, "policy_interest_rate_percent": 16.5,
        "usd_lkr_exchange_rate": 355.0, "gdp_growth_rate_percent": -10.0, "attrition": False,
    }


def test_validation_passes_for_a_complete_consistent_dataset():
    report = validate_integrated_dataset(
        [{"id": "employee-1"}], [{"indicator_month": "2023-03-01"}],
        [{"employee_record_id": "employee-1", "mapping_status": "mapped"}], [_valid_record()],
    )

    assert report["validation_status"] == "passed"
    assert report["missing_value_count"] == 0
    assert report["duplicate_records"] == 0
    assert report["unmatched_records"] == 0
    assert report["mapping_rate"] == 100.0
    assert report["integration_rate"] == 100.0


def test_validation_reports_missing_invalid_duplicate_and_unmatched_records():
    invalid = {**_valid_record(), "employee_id": "EMP002", "salary": None, "age": 120}
    report = validate_integrated_dataset(
        [{"id": "employee-1"}, {"id": "employee-2"}], [{"indicator_month": "2023-03-01"}],
        [{"employee_record_id": "employee-1", "mapping_status": "mapped"}, {"employee_record_id": "employee-2", "mapping_status": "unmapped"}],
        [_valid_record(), invalid],
    )

    assert report["validation_status"] == "failed"
    assert report["missing_values"] == {"salary": 1}
    assert report["duplicate_records"] == 1
    assert report["unmatched_records"] == 1
    assert report["invalid_value_count"] >= 2
    assert report["record_count_consistency"]["is_consistent"] is False
