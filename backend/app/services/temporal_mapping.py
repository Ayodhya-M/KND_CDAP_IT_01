from __future__ import annotations

from datetime import date
from typing import Any


def first_day_of_month(value: str) -> str | None:
    """Convert an ISO observation date to the matching monthly indicator key."""
    try:
        observed = date.fromisoformat(value)
    except (TypeError, ValueError):
        return None
    return observed.replace(day=1).isoformat()


def build_monthly_mappings(
    employees: list[dict[str, Any]], economic_indicators: list[dict[str, Any]], mapping_run_id: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Map employees to monthly indicators using observation_date only."""
    indicators_by_month = {indicator["indicator_month"]: indicator for indicator in economic_indicators}
    database_rows: list[dict[str, Any]] = []
    preview_rows: list[dict[str, Any]] = []
    matched = 0

    for employee in employees:
        observation_date = employee.get("observation_date")
        mapped_month = first_day_of_month(observation_date)
        indicator = indicators_by_month.get(mapped_month) if mapped_month else None
        mapping_status = "mapped" if indicator else ("invalid_date" if mapped_month is None else "unmapped")
        if indicator:
            matched += 1
        database_rows.append({
            "mapping_run_id": mapping_run_id,
            "employee_record_id": employee["id"],
            "economic_indicator_id": indicator["id"] if indicator else None,
            "employee_event_date": observation_date,
            "mapped_month": mapped_month,
            "mapping_status": mapping_status,
        })
        preview_rows.append({
            "employee_id": employee["employee_id"],
            "observation_date": observation_date,
            "economic_month": mapped_month,
            "status": mapping_status,
        })

    total = len(employees)
    summary = {
        "total_employee_records": total,
        "matched_records": matched,
        "unmatched_records": total - matched,
        "mapping_rate": round((matched / total) * 100, 2) if total else 0,
    }
    return database_rows, preview_rows, summary
