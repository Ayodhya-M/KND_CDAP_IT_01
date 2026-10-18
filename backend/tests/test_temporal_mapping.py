from pathlib import Path

import pandas as pd

from app.main import app
from app.services.temporal_mapping import build_monthly_mappings, first_day_of_month


def test_temporal_mapping_router_is_registered():
    routes = {(route.path, tuple(route.methods or [])) for route in app.routes}
    assert ("/api/v1/temporal-mapping/uploads", ("GET",)) in routes
    assert ("/api/v1/temporal-mapping/preview", ("POST",)) in routes


def test_observation_date_is_normalised_to_first_day_of_month():
    assert first_day_of_month("2023-03-17") == "2023-03-01"
    assert first_day_of_month("not-a-date") is None


def test_all_pilot_employees_map_to_their_matching_economic_month():
    project_root = Path(__file__).parents[2]
    hr_data = pd.read_csv(project_root / "pilot-data" / "module1_hr_pilot_100_employees.csv")
    macro_data = pd.read_csv(project_root / "pilot-data" / "module1_sri_lanka_macro_pilot_6_months.csv")
    employees = [
        {"id": f"employee-{index}", "employee_id": row.EmployeeID, "observation_date": row.ObservationDate}
        for index, row in enumerate(hr_data.itertuples(index=False), start=1)
    ]
    indicators = [
        {"id": f"indicator-{index}", "indicator_month": pd.Timestamp(row.Date).date().isoformat()}
        for index, row in enumerate(macro_data.itertuples(index=False), start=1)
    ]

    stored_rows, preview_rows, summary = build_monthly_mappings(employees, indicators, "mapping-run-1")

    assert len(stored_rows) == 100
    assert len(preview_rows) == 100
    assert summary == {"total_employee_records": 100, "matched_records": 100, "unmatched_records": 0, "mapping_rate": 100.0}
    assert {row["economic_month"] for row in preview_rows} == {
        "2023-01-01", "2023-02-01", "2023-03-01", "2023-04-01", "2023-05-01", "2023-06-01",
    }
    assert {row["status"] for row in preview_rows} == {"mapped"}


def test_missing_economic_month_is_reported_as_unmatched():
    stored_rows, preview_rows, summary = build_monthly_mappings(
        [{"id": "employee-1", "employee_id": "EMP001", "observation_date": "2023-04-08"}],
        [{"id": "indicator-1", "indicator_month": "2023-03-01"}],
        "mapping-run-1",
    )

    assert stored_rows[0]["economic_indicator_id"] is None
    assert preview_rows[0]["status"] == "unmapped"
    assert summary == {"total_employee_records": 1, "matched_records": 0, "unmatched_records": 1, "mapping_rate": 0.0}
