"""Prepare local LFS microdata and return aggregate-only research results."""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from datetime import date, timedelta
from pathlib import Path
from statistics import mean
from typing import Any

from app.services.eesi import FORMULAS, calculate, finite_number

ROOT = Path(__file__).resolve().parents[3]
REAL_VERSION = "pp1-lfs2024-v1"
REAL_BOUNDS = {"inflation": (-1.7, 6.5), "cpi": (202.1, 215.0), "unemployment": (4.2, 4.7)}
SOURCES = [
    {"title": "DCS Labour Force Survey 2024", "url": "https://nada.statistics.gov.lk/index.php/catalog/490/study-description"},
    {"title": "LFS 2024 questionnaire, Q45 (PDF page 15)", "url": "https://nada.statistics.gov.lk/index.php/catalog/490/download/4578"},
    {"title": "DCS NCPI movements, headline index and year-on-year inflation, base 2021=100", "url": "https://www.statistics.gov.lk/Resource/en/InflationAndPrices/NCPI/MovementsofNCPIandNCPI-Core.pdf"},
    {"title": "LFS 2024 Q4, Selected Labour Force Indicators (PDF page 8)", "url": "https://www.statistics.gov.lk/Resource/en/LabourForce/Quarterly_Reports/2024Q4report.pdf"},
]


def prior_month(year: Any, month: Any) -> str:
    year_value = finite_number(year, "year")
    month_value = finite_number(month, "month")
    if not year_value.is_integer() or not month_value.is_integer():
        raise ValueError("Survey year and month must be integers")
    return (date(int(year_value), int(month_value), 1) - timedelta(days=1)).strftime("%Y-%m")


def prepare_employee(row: dict[str, str], economic: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if finite_number(row["AGE"], "age") < 15:
        raise ValueError("outside_survey_working_age")
    if row["Q45"].strip() != "1":
        raise ValueError("not_main_job_employee")
    # A populated Q45_A_1 identifies the monthly-salary branch. Do not use
    # daily wages, self-employment income, or expected job-seeker income Q57.
    if not row["Q45_A_1"].strip():
        raise ValueError("no_monthly_gross_salary")
    salary = finite_number(row["Q45_A_1"].strip(), "gross salary")
    if salary <= 0:
        raise ValueError("nonpositive_gross_salary")
    weight = finite_number(row["AnnualFactor_25Percent"], "survey weight")
    if weight <= 0:
        raise ValueError("nonpositive_weight")
    if finite_number(row["YEAR"], "year") != 2024:
        raise ValueError("outside_2024_survey")
    income_month = prior_month(row["YEAR"], row["MONTH"])
    if income_month not in economic:
        raise ValueError("missing_economic_month")
    macro = economic[income_month]
    result = calculate(salary, macro["inflation"], macro["cpi"], macro["unemployment"], bounds=REAL_BOUNDS, version=REAL_VERSION)
    return {"salary": salary, "weight": weight, "income_month": income_month, "survey_month": f"2024-{int(float(row['MONTH'])):02}", "scores": result["scores"]}


def salary_band(salary: float) -> str:
    if salary < 25000:
        return "Below 25,000"
    if salary < 50000:
        return "25,000 to below 50,000"
    if salary < 75000:
        return "50,000 to below 75,000"
    if salary < 100000:
        return "75,000 to below 100,000"
    return "100,000 and above"


def summarize(rows: list[dict[str, Any]], label: str) -> dict[str, Any]:
    if len(rows) < 30:
        return {"label": label, "suppressed": True, "count": None, "scores": None}
    total_weight = sum(row["weight"] for row in rows)
    return {"label": label, "suppressed": False, "count": len(rows), "scores": {
        formula["id"]: {
            "sample_mean": round(mean(row["scores"][formula["id"]] for row in rows), 4),
            "weighted_mean": round(sum(row["scores"][formula["id"]] * row["weight"] for row in rows) / total_weight, 4),
        } for formula in FORMULAS
    }}


def build_real_summary(source: Path, prepared_output: Path | None = None) -> dict[str, Any]:
    reference_path = ROOT / "data/reference/eesi/economic-reference.csv"
    with reference_path.open(encoding="utf-8-sig", newline="") as stream:
        economic_rows = list(csv.DictReader(stream))
    economic = {row["income_month"]: row for row in economic_rows}
    if len(economic) != 12:
        raise ValueError("Economic reference must contain twelve unique income months")
    with source.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        required = {"YEAR", "MONTH", "AGE", "Q45", "Q45_A_1", "AnnualFactor_25Percent"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("Required LFS columns are missing")
        original = list(reader)
    rows = []
    exclusions: Counter[str] = Counter()
    for row in original:
        try:
            rows.append(prepare_employee(row, economic))
        except (ValueError, KeyError) as error:
            exclusions[str(error)] += 1
    if not rows:
        raise ValueError("No eligible monthly salaried employees")
    if prepared_output:
        # This intermediate is private and intentionally has no linkage IDs,
        # household keys, location, demographics or individual public export.
        prepared_output.parent.mkdir(parents=True, exist_ok=True)
        with prepared_output.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=["survey_month", "income_month", "salary", "weight", "economic", "additive", "interaction"])
            writer.writeheader()
            for row in rows:
                writer.writerow({key: row[key] for key in ["survey_month", "income_month", "salary", "weight"]} | row["scores"])
    return {
        "version": REAL_VERSION, "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "economic_reference_sha256": hashlib.sha256(reference_path.read_bytes()).hexdigest(),
        "source_records": len(original), "eligible_records": len(rows), "excluded_records": len(original) - len(rows), "exclusions": dict(exclusions),
        "formulas": FORMULAS, "bounds": REAL_BOUNDS, "reference_salary": 50000,
        "overall": summarize(rows, "All eligible monthly salaried employees"),
        "by_month": [summarize([row for row in rows if row["income_month"] == month], month) for month in sorted(economic)],
        "by_salary_band": [summarize([row for row in rows if salary_band(row["salary"]) == band], band) for band in ["Below 25,000", "25,000 to below 50,000", "50,000 to below 75,000", "75,000 to below 100,000", "100,000 and above"]],
        "economic_months": economic_rows, "sources": SOURCES,
        "notes": [
            "Real anonymized LFS 2024 monthly salaried employees aged 15+ with positive main-job gross salary and survey weight.",
            "Gross salary includes allowances; overtime, in-kind income, secondary income, daily wages and self-employment income are excluded.",
            "Assumption: MONTH is interview month and last month means the preceding calendar month. Exact interview dates are unavailable; confirm against DCS documentation before final research.",
            "Income months December 2023 to November 2024; NCPI is national headline, base 2021=100; inflation is year-on-year percent.",
            "Unemployment uses the published rate for each income month's quarter, repeated without interpolation; this is retrospective, not a live prediction experiment.",
            "Reference ranges are frozen from these twelve economic months. Results are not comparable with the synthetic pilot's different reference scale.",
            "AnnualFactor_25Percent supplies descriptive weights. No national totals, confidence intervals or representative-population claims are made for this salary-complete subset.",
            "Only aggregates are exposed; groups below 30 respondents are suppressed. Different monthly samples are not repeated observations of the same employees.",
            "EESI scores remain exploratory. Independent financial-stress validation, formula selection and sensitivity analysis remain outstanding.",
        ],
    }


def load_real_summary() -> dict[str, Any]:
    return json.loads((ROOT / "docs/eesi/lfs2024-aggregate.json").read_text(encoding="utf-8"))
