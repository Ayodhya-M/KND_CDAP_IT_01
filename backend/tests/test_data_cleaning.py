from app.main import app
from app.services.data_cleaning import missing_value_summary, rows_without_required_missing_values


def test_data_cleaning_router_is_registered():
    routes = {(route.path, tuple(route.methods or [])) for route in app.routes}
    assert ("/api/v1/data-cleaning/uploads", ("GET",)) in routes
    assert ("/api/v1/data-cleaning/analyse/{upload_id}", ("GET",)) in routes
    assert ("/api/v1/data-cleaning/remove-missing", ("POST",)) in routes


def test_hr_missing_value_analysis_and_safe_row_removal():
    complete = {
        "employee_id": "EMP001", "age": 30, "salary": 50000, "department": "Sales",
        "join_date": "2020-01-01", "observation_date": "2023-03-01", "attrition": False,
        "gender": "Female", "job_role": "Sales Executive", "job_level": 2,
        "business_travel": "Travel_Rarely", "distance_from_home": 5,
        "education_field": "Marketing", "marital_status": "Single", "overtime": False,
        "job_satisfaction": 3, "environment_satisfaction": 3, "work_life_balance": 3,
        "total_working_years": 7, "years_at_company": 3,
    }
    missing_salary = {**complete, "employee_id": "EMP002", "salary": None}

    summary = missing_value_summary([complete, missing_salary], "hr")

    assert summary["total_records"] == 2
    assert summary["rows_with_missing_values"] == 1
    assert summary["missing_values"] == {"salary": 1}
    assert rows_without_required_missing_values([complete, missing_salary], "hr") == [complete]


def test_economic_cleaning_does_not_treat_zero_as_missing():
    row = {
        "indicator_month": "2023-01-01", "inflation_rate": 0, "unemployment_rate": 0,
        "cost_of_living_index": 0, "cpi_index": 0, "policy_interest_rate_percent": 0,
        "usd_lkr_exchange_rate": 0, "gdp_growth_rate_percent": 0,
    }

    assert missing_value_summary([row], "economic")["missing_values"] == {}
    assert rows_without_required_missing_values([row], "economic") == [row]
