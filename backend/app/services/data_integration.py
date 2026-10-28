from __future__ import annotations

from typing import Any


def build_integrated_records(
    temporal_mappings: list[dict[str, Any]],
    employees: list[dict[str, Any]],
    economic_indicators: list[dict[str, Any]],
    integration_run_id: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    """Combine HR and economic values only through an existing temporal mapping."""
    employees_by_id = {employee["id"]: employee for employee in employees}
    indicators_by_id = {indicator["id"]: indicator for indicator in economic_indicators}
    records: list[dict[str, Any]] = []
    previews: list[dict[str, Any]] = []
    skipped = 0

    for mapping in temporal_mappings:
        employee = employees_by_id.get(mapping.get("employee_record_id"))
        indicator = indicators_by_id.get(mapping.get("economic_indicator_id"))
        if mapping.get("mapping_status") != "mapped" or not employee or not indicator:
            skipped += 1
            continue

        record = {
            "integration_run_id": integration_run_id,
            "employee_record_id": employee["id"],
            "economic_indicator_id": indicator["id"],
            "temporal_mapping_id": mapping["id"],
            "employee_id": employee["employee_id"],
            "observation_date": employee["observation_date"],
            "mapped_month": mapping["mapped_month"],
            "age": employee.get("age"),
            "salary": employee.get("salary"),
            "tenure_years": employee.get("years_at_company"),
            "additional_income": employee.get("additional_income"),
            "department": employee.get("department"),
            "gender": employee.get("gender"),
            "job_role": employee.get("job_role"),
            "job_level": employee.get("job_level"),
            "overtime": employee.get("overtime"),
            "job_satisfaction": employee.get("job_satisfaction"),
            "work_life_balance": employee.get("work_life_balance"),
            "inflation_rate": indicator.get("inflation_rate"),
            "unemployment_rate": indicator.get("unemployment_rate"),
            "cost_of_living_index": indicator.get("cost_of_living_index"),
            "cpi_index": indicator.get("cpi_index"),
            "policy_interest_rate_percent": indicator.get("policy_interest_rate_percent"),
            "usd_lkr_exchange_rate": indicator.get("usd_lkr_exchange_rate"),
            "gdp_growth_rate_percent": indicator.get("gdp_growth_rate_percent"),
            "attrition": employee["attrition"],
        }
        records.append(record)
        previews.append({
            "employee_id": record["employee_id"],
            "salary": record["salary"],
            "tenure_years": record["tenure_years"],
            "additional_income": record["additional_income"],
            "overtime": record["overtime"],
            "job_satisfaction": record["job_satisfaction"],
            "observation_date": record["observation_date"],
            "economic_month": record["mapped_month"],
            "inflation_rate": record["inflation_rate"],
            "cpi_index": record["cpi_index"],
            "unemployment_rate": record["unemployment_rate"],
            "policy_interest_rate_percent": record["policy_interest_rate_percent"],
            "usd_lkr_exchange_rate": record["usd_lkr_exchange_rate"],
            "gdp_growth_rate_percent": record["gdp_growth_rate_percent"],
            "attrition": record["attrition"],
        })

    return records, previews, skipped
