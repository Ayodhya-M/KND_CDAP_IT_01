from __future__ import annotations

from datetime import date
from typing import Any


REQUIRED_INTEGRATED_FIELDS = [
    "employee_id", "age", "salary", "additional_income", "overtime", "tenure_years",
    "observation_date", "mapped_month", "inflation_rate", "cpi_index",
    "cost_of_living_index", "unemployment_rate", "policy_interest_rate_percent",
    "usd_lkr_exchange_rate", "gdp_growth_rate_percent", "attrition",
]


def _missing(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _as_number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _date_is_valid(value: Any, first_day_required: bool = False) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return False
    return not first_day_required or parsed.day == 1


def validate_integrated_dataset(
    hr_records: list[dict[str, Any]],
    economic_indicators: list[dict[str, Any]],
    temporal_mappings: list[dict[str, Any]],
    integrated_records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Return a read-only quality report for one integration run."""
    missing_values = {
        field: sum(_missing(record.get(field)) for record in integrated_records)
        for field in REQUIRED_INTEGRATED_FIELDS
    }
    missing_values = {field: count for field, count in missing_values.items() if count}

    employee_record_ids = [record.get("employee_record_id") for record in integrated_records]
    employee_ids = [record.get("employee_id") for record in integrated_records]
    duplicate_record_count = (len(employee_record_ids) - len(set(employee_record_ids))) + (len(employee_ids) - len(set(employee_ids)))

    invalid_by_field: dict[str, list[str]] = {}

    def add_invalid(field: str, record: dict[str, Any]) -> None:
        invalid_by_field.setdefault(field, []).append(str(record.get("employee_id") or record.get("employee_record_id") or "unknown"))

    for record in integrated_records:
        age = _as_number(record.get("age"))
        if age is None or age < 14 or age > 100:
            add_invalid("age", record)
        for field in ("salary", "additional_income", "tenure_years"):
            value = _as_number(record.get(field))
            if value is None or value < 0:
                add_invalid(field, record)
        for field in ("inflation_rate", "cpi_index", "cost_of_living_index", "unemployment_rate", "policy_interest_rate_percent", "usd_lkr_exchange_rate"):
            value = _as_number(record.get(field))
            if value is None or value < 0:
                add_invalid(field, record)
        if _as_number(record.get("gdp_growth_rate_percent")) is None:
            add_invalid("gdp_growth_rate_percent", record)
        if not _date_is_valid(record.get("observation_date")):
            add_invalid("observation_date", record)
        if not _date_is_valid(record.get("mapped_month"), first_day_required=True):
            add_invalid("mapped_month", record)

    invalid_values = [
        {"field": field, "count": len(record_ids), "sample_employee_ids": record_ids[:10]}
        for field, record_ids in invalid_by_field.items()
    ]
    mapped_count = sum(mapping.get("mapping_status") == "mapped" for mapping in temporal_mappings)
    unmatched_count = len(temporal_mappings) - mapped_count
    total_hr_records = len(hr_records)
    mapping_rate = round((mapped_count / total_hr_records) * 100, 2) if total_hr_records else 0
    integration_rate = round((len(integrated_records) / total_hr_records) * 100, 2) if total_hr_records else 0
    consistency = {
        "hr_records_equal_mapping_records": total_hr_records == len(temporal_mappings),
        "integrated_records_equal_mapped_records": len(integrated_records) == mapped_count,
        "expected_integrated_records": mapped_count,
        "actual_integrated_records": len(integrated_records),
    }
    consistency["is_consistent"] = all(value for key, value in consistency.items() if key.startswith(("hr_records", "integrated_records")))
    passed = not missing_values and duplicate_record_count == 0 and not invalid_values and unmatched_count == 0 and consistency["is_consistent"]

    return {
        "total_hr_records": total_hr_records,
        "economic_months": len({record.get("indicator_month") for record in economic_indicators}),
        "integrated_records": len(integrated_records),
        "missing_values": missing_values,
        "missing_value_count": sum(missing_values.values()),
        "duplicate_records": duplicate_record_count,
        "invalid_values": invalid_values,
        "invalid_value_count": sum(item["count"] for item in invalid_values),
        "unmatched_records": unmatched_count,
        "mapping_rate": mapping_rate,
        "integration_rate": integration_rate,
        "record_count_consistency": consistency,
        "validation_status": "passed" if passed else "failed",
    }
