from __future__ import annotations

from typing import Any


REQUIRED_FIELDS = {
    "hr": [
        "employee_id", "age", "salary", "department", "join_date",
        "observation_date", "attrition", "gender", "job_role", "job_level",
        "business_travel", "distance_from_home", "education_field",
        "marital_status", "overtime", "job_satisfaction",
        "environment_satisfaction", "work_life_balance", "total_working_years",
        "years_at_company",
    ],
    "economic": [
        "indicator_month", "inflation_rate", "unemployment_rate",
        "cost_of_living_index", "cpi_index", "policy_interest_rate_percent",
        "usd_lkr_exchange_rate", "gdp_growth_rate_percent",
    ],
}


def is_missing(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def missing_value_summary(rows: list[dict[str, Any]], dataset_type: str) -> dict[str, Any]:
    required_fields = REQUIRED_FIELDS[dataset_type]
    missing_by_field = {
        field: sum(is_missing(row.get(field)) for row in rows)
        for field in required_fields
    }
    missing_by_field = {field: count for field, count in missing_by_field.items() if count}
    rows_with_missing = [
        index + 1 for index, row in enumerate(rows)
        if any(is_missing(row.get(field)) for field in required_fields)
    ]
    return {
        "total_records": len(rows),
        "rows_with_missing_values": len(rows_with_missing),
        "missing_values": missing_by_field,
        "sample_row_numbers": rows_with_missing[:10],
    }


def rows_without_required_missing_values(rows: list[dict[str, Any]], dataset_type: str) -> list[dict[str, Any]]:
    required_fields = REQUIRED_FIELDS[dataset_type]
    return [
        row for row in rows
        if not any(is_missing(row.get(field)) for field in required_fields)
    ]


def copy_row_for_clean_upload(row: dict[str, Any], cleaned_upload_id: str) -> dict[str, Any]:
    excluded = {"id", "upload_id", "created_at"}
    return {key: value for key, value in row.items() if key not in excluded} | {"upload_id": cleaned_upload_id}
