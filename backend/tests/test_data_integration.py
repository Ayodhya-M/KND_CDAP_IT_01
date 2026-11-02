from app.main import app
from app.services.data_integration import build_integrated_records


def test_integration_router_is_registered():
    routes = {(route.path, tuple(route.methods or [])) for route in app.routes}
    assert ("/api/v1/integration/mapping-runs", ("GET",)) in routes
    assert ("/api/v1/integration/generate", ("POST",)) in routes


def test_temporal_mapping_creates_a_unified_employee_record():
    employee = {
        "id": "employee-1", "employee_id": "EMP001", "age": 32, "salary": 120000, "additional_income": 12000,
        "department": "Sales", "gender": "Female", "job_role": "Sales Executive",
        "job_level": 2, "overtime": True, "job_satisfaction": 2,
        "work_life_balance": 3, "years_at_company": 4, "observation_date": "2023-03-17", "attrition": False,
    }
    indicator = {
        "id": "economic-3", "inflation_rate": 50.3, "unemployment_rate": 4.8,
        "cost_of_living_index": 108.59, "cpi_index": 108.59,
        "policy_interest_rate_percent": 16.5, "usd_lkr_exchange_rate": 355.0,
        "gdp_growth_rate_percent": -10.0,
    }
    mapping = {
        "id": "mapping-1", "employee_record_id": "employee-1", "economic_indicator_id": "economic-3",
        "mapped_month": "2023-03-01", "mapping_status": "mapped",
    }

    records, preview, skipped = build_integrated_records([mapping], [employee], [indicator], "integration-1")

    assert skipped == 0
    assert len(records) == 1
    assert records[0]["employee_id"] == "EMP001"
    assert records[0]["observation_date"] == "2023-03-17"
    assert records[0]["mapped_month"] == "2023-03-01"
    assert records[0]["job_satisfaction"] == 2
    assert records[0]["tenure_years"] == 4
    assert records[0]["additional_income"] == 12000
    assert records[0]["inflation_rate"] == 50.3
    assert records[0]["usd_lkr_exchange_rate"] == 355.0
    assert preview[0]["attrition"] is False


def test_unmapped_employee_is_not_added_to_unified_dataset():
    mapping = {"id": "mapping-1", "employee_record_id": "employee-1", "economic_indicator_id": None, "mapping_status": "unmapped"}
    records, preview, skipped = build_integrated_records([mapping], [{"id": "employee-1"}], [], "integration-1")

    assert records == []
    assert preview == []
    assert skipped == 1
