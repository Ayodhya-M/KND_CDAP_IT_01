"""Versioned PP1 candidate indices. No database or outcome labels are used."""
from __future__ import annotations

import csv
import math
from datetime import date
from pathlib import Path
from statistics import mean
from typing import Any

VERSION = "pp1-exploratory-v1"
# Frozen from the supplied pilot file, not fitted to each employee batch.
BOUNDS = {"inflation": (12.0, 53.2), "cpi": (100.0, 115.27), "unemployment": (4.6, 4.8)}
FORMULAS = [
    {"id": "economic", "name": "Economic baseline", "expression": "100 × (I + C + U) / 3", "rationale": "Equal weights provide a transparent economic-only comparator; salary has no effect."},
    {"id": "additive", "name": "Additive salary exposure", "expression": "100 × (I + C + U + V) / 4", "rationale": "Treat income exposure as a separate equally weighted component. This is a hypothesis, not a validated weighting."},
    {"id": "interaction", "name": "Salary interaction", "expression": "100 × ((I + C + U) / 3) × V", "rationale": "Test whether salary moderates economic pressure. It becomes zero when normalized economic pressure is zero, a limitation to evaluate."},
]


def finite_number(value: Any, name: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name} must be numeric") from error
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def calculate(salary: float, inflation: float, cpi: float, unemployment: float, reference_salary: float = 50000, *, bounds: dict[str, tuple[float, float]] | None = None, version: str = VERSION) -> dict[str, Any]:
    reference_bounds = BOUNDS if bounds is None else bounds
    if set(reference_bounds) != set(BOUNDS):
        raise ValueError("Reference bounds must define inflation, cpi and unemployment")
    for low, high in reference_bounds.values():
        if not math.isfinite(low) or not math.isfinite(high) or high <= low:
            raise ValueError("Reference ranges must be finite and nonconstant")
    values = {key: finite_number(value, key) for key, value in {"salary": salary, "inflation": inflation, "cpi": cpi, "unemployment": unemployment, "reference_salary": reference_salary}.items()}
    if values["salary"] <= 0 or values["reference_salary"] <= 0:
        raise ValueError("Salary and reference salary must be greater than zero")
    if values["cpi"] <= 0 or not 0 <= values["unemployment"] <= 100:
        raise ValueError("CPI must be positive and unemployment must be between 0 and 100")
    components = {}
    warnings = []
    for key, (low, high) in reference_bounds.items():
        value = values[key]
        components[key] = max(0.0, min(1.0, (value - low) / (high - low)))
        if not low <= value <= high:
            warnings.append(f"{key} is outside the reference range; its normalized value was clipped")
    # Ratio form avoids overflow when both finite salaries are very large.
    if values["salary"] <= values["reference_salary"]:
        vulnerability = 1 / (1 + values["salary"] / values["reference_salary"])
    else:
        ratio = values["reference_salary"] / values["salary"]
        vulnerability = ratio / (1 + ratio)
    components["salary_exposure"] = vulnerability
    economic = mean(components[key] for key in BOUNDS)
    scores = {"economic": 100 * economic, "additive": 100 * (3 * economic + vulnerability) / 4, "interaction": 100 * economic * vulnerability}
    contributions = {
        "economic": {key: 100 * components[key] / 3 for key in BOUNDS},
        "additive": {key: 25 * value for key, value in components.items()},
        "interaction": {key: 100 * components[key] * vulnerability / 3 for key in BOUNDS},
    }
    return {"inputs": values, "components": components, "scores": scores, "contributions": contributions, "warnings": warnings, "version": version}


def metadata() -> dict[str, Any]:
    return {"version": VERSION, "formulas": FORMULAS, "bounds": BOUNDS, "reference_salary": 50000, "reference_period": "2023-01 to 2023-06", "normalization": "clip((x - lower) / (upper - lower), 0, 1)", "salary_exposure": "V = reference salary / (reference salary + employee salary)", "validation_status": "Exploratory prototype; no empirical accuracy established", "limitations": ["Pilot reference ranges are not clinical or population thresholds.", "CPI and inflation may overlap; indicator ablation is still required.", "Positive unemployment direction is an assumed insecurity channel, not a turnover claim.", "Salary is not disposable household income; debt, dependents and expenses are absent.", "No formula has been selected as the final EESI."]}


def pilot_preview(size: int = 100) -> dict[str, Any]:
    if size not in (100, 300):
        raise ValueError('Pilot size must be 100 or 300')
    root = Path(__file__).resolve().parents[3] / "pilot-data"
    with (root / "module1_sri_lanka_macro_pilot_6_months.csv").open(encoding="utf-8-sig", newline="") as stream:
        months = list(csv.DictReader(stream))
    indicators = {row["Date"][:7]: row for row in months}
    with (root / f"module1_hr_pilot_{size}_employees.csv").open(encoding="utf-8-sig", newline="") as stream:
        employees = list(csv.DictReader(stream))
    rows, rejected = [], []
    for row in employees:
        try:
            month = date.fromisoformat(row["ObservationDate"]).strftime("%Y-%m")
            if month not in indicators:
                raise ValueError("No economic indicators for observation month")
            macro = indicators[month]
            result = calculate(row["MonthlyIncome"], macro["Inflation_Rate_Percent"], macro["CPI_Index"], macro["Unemployment_Rate_Percent"])
            rows.append({"employee_id": row["EmployeeID"], "month": month, **result})
        except (KeyError, ValueError) as error:
            rejected.append({"employee_id": row.get("EmployeeID", "unknown"), "reason": str(error)})
    summary = {formula["id"]: {"mean": mean(row["scores"][formula["id"]] for row in rows), "min": min(row["scores"][formula["id"]] for row in rows), "max": max(row["scores"][formula["id"]] for row in rows)} for formula in FORMULAS} if rows else {}
    return {"metadata": metadata(), "rows": rows, "rejected": rejected, "summary": summary, "months": months, "data_note": f"{size} synthetic HR records; supplied economic pilot values have not been independently verified."}
