"""Pilot-only Module 1/2 export for Module 3 integration demonstrations."""
from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path

from app.services.eesi import FORMULAS, VERSION, calculate


PILOT_ROOT = Path(__file__).resolve().parents[3] / "pilot-data"
FEATURE_COLUMNS = [
    "Age",
    "MonthlyIncome",
    "OverTime",
    "JobSatisfaction",
    "JobLevel",
    "YearsAtCompany",
    "Department",
    "EESI",
]
TARGET_COLUMN = "Attrition"
EXPORT_COLUMNS = [
    "EmployeeID",
    "ObservationMonth",
    *FEATURE_COLUMNS,
    TARGET_COLUMN,
    "EESIFormulaId",
    "EESIFormulaVersion",
]
SUPPORTED_FORMULA_IDS = {formula["id"] for formula in FORMULAS}


def export_contract() -> dict[str, object]:
    return {
        "contract_version": "module3-pp1-pilot-v1",
        "dataset_kind": "synthetic_pilot_only",
        "purpose": "Technical integration demonstration only; not valid for reporting research performance.",
        "identifier": "EmployeeID is a synthetic pilot identifier and must not be used as a model feature.",
        "observation_month": "Derived from Module 1 ObservationDate as YYYY-MM.",
        "target_column": TARGET_COLUMN,
        "feature_columns": FEATURE_COLUMNS,
        "eesi": {
            "column": "EESI",
            "formula_id_column": "EESIFormulaId",
            "formula_version_column": "EESIFormulaVersion",
            "supported_formula_ids": sorted(SUPPORTED_FORMULA_IDS),
            "requirement": "Choose one formula explicitly for a training/export run and retain its ID and version with all predictions.",
        },
    }


def build_pilot_export(formula_id: str) -> list[dict[str, str | float | int]]:
    if formula_id not in SUPPORTED_FORMULA_IDS:
        supported = ", ".join(sorted(SUPPORTED_FORMULA_IDS))
        raise ValueError(f"Unsupported formula_id '{formula_id}'. Choose one of: {supported}.")

    with (PILOT_ROOT / "module1_sri_lanka_macro_pilot_6_months.csv").open(encoding="utf-8-sig", newline="") as stream:
        macro_by_month = {row["Date"][:7]: row for row in csv.DictReader(stream)}
    with (PILOT_ROOT / "module1_hr_pilot_100_employees.csv").open(encoding="utf-8-sig", newline="") as stream:
        employees = list(csv.DictReader(stream))

    rows = []
    for employee in employees:
        observation_month = employee["ObservationDate"][:7]
        macro = macro_by_month.get(observation_month)
        if macro is None:
            raise ValueError(f"No pilot macroeconomic row exists for {observation_month}.")
        result = calculate(
            salary=float(employee["MonthlyIncome"]),
            inflation=float(macro["Inflation_Rate_Percent"]),
            cpi=float(macro["CPI_Index"]),
            unemployment=float(macro["Unemployment_Rate_Percent"]),
        )
        rows.append({
            "EmployeeID": employee["EmployeeID"],
            "ObservationMonth": observation_month,
            "Age": int(employee["Age"]),
            "MonthlyIncome": float(employee["MonthlyIncome"]),
            "OverTime": employee["OverTime"],
            "JobSatisfaction": int(employee["JobSatisfaction"]),
            "JobLevel": int(employee["JobLevel"]),
            "YearsAtCompany": int(employee["YearsAtCompany"]),
            "Department": employee["Department"],
            "EESI": round(float(result["scores"][formula_id]), 6),
            "Attrition": employee["Attrition"],
            "EESIFormulaId": formula_id,
            "EESIFormulaVersion": VERSION,
        })
    return rows


def pilot_export_csv(formula_id: str) -> str:
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=EXPORT_COLUMNS)
    writer.writeheader()
    writer.writerows(build_pilot_export(formula_id))
    return output.getvalue()
