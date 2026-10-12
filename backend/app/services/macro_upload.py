from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import Any

import pandas as pd


REQUIRED_COLUMNS = [
    "Date", "Year", "Month", "Inflation_Rate_Percent", "CPI_Index",
    "Unemployment_Rate_Percent", "Policy_Interest_Rate_Percent",
    "USD_LKR_Exchange_Rate", "GDP_Growth_Rate_Percent",
]
PILOT_START = pd.Timestamp("2023-01-01")
PILOT_END = pd.Timestamp("2023-06-01")
NON_NEGATIVE_COLUMNS = [
    "Inflation_Rate_Percent", "CPI_Index", "Unemployment_Rate_Percent",
    "Policy_Interest_Rate_Percent", "USD_LKR_Exchange_Rate",
]


@dataclass
class MacroValidationResult:
    dataframe: pd.DataFrame | None
    summary: dict[str, Any]

    @property
    def is_valid(self) -> bool:
        return self.dataframe is not None and self.summary["invalid_records"] == 0


def _sample_rows(indexes: list[int]) -> list[int]:
    return [index + 2 for index in indexes[:10]]


def validate_macro_csv(content: bytes, filename: str) -> MacroValidationResult:
    if not content.strip():
        return MacroValidationResult(None, {"status": "validation_failed", "file_name": filename, "errors": [{"field": "file", "message": "CSV file is empty"}]})
    try:
        dataframe = pd.read_csv(BytesIO(content), dtype=str, keep_default_na=False)
    except pd.errors.EmptyDataError:
        return MacroValidationResult(None, {"status": "validation_failed", "file_name": filename, "errors": [{"field": "file", "message": "CSV file is empty"}]})
    except Exception as error:
        return MacroValidationResult(None, {"status": "validation_failed", "file_name": filename, "errors": [{"field": "file", "message": f"CSV could not be read: {error}"}]})

    dataframe.columns = [str(column).strip() for column in dataframe.columns]
    dataframe = dataframe.map(lambda value: value.strip() if isinstance(value, str) else value)
    if dataframe.empty:
        return MacroValidationResult(None, {"status": "validation_failed", "file_name": filename, "errors": [{"field": "file", "message": "CSV contains headers but no economic records"}]})

    missing_columns = [column for column in REQUIRED_COLUMNS if column not in dataframe.columns]
    if missing_columns:
        return MacroValidationResult(None, {"status": "validation_failed", "file_name": filename, "total_records": len(dataframe), "errors": [{"field": "columns", "message": "Required columns are missing", "columns": missing_columns}]})

    errors: list[dict[str, Any]] = []
    invalid_rows: set[int] = set()

    def add_error(field: str, message: str, indexes: list[int]) -> None:
        if indexes:
            invalid_rows.update(indexes)
            errors.append({"field": field, "message": message, "count": len(indexes), "sample_rows": _sample_rows(indexes)})

    missing_values: dict[str, int] = {}
    for column in dataframe.columns:
        indexes = dataframe.index[dataframe[column].eq("")].tolist()
        if indexes:
            missing_values[column] = len(indexes)
            if column in REQUIRED_COLUMNS:
                add_error(column, "Required value is missing", indexes)

    dates = pd.to_datetime(dataframe["Date"], format="%Y-%m-%d", errors="coerce")
    add_error("Date", "Date must use YYYY-MM-DD", dataframe.index[dataframe["Date"].ne("") & dates.isna()].tolist())
    add_error("Date", "Date must be the first day of a month", dataframe.index[dates.notna() & dates.dt.day.ne(1)].tolist())
    add_error("Date", "Date must be between 2023-01-01 and 2023-06-01", dataframe.index[dates.notna() & ((dates < PILOT_START) | (dates > PILOT_END))].tolist())
    duplicate_dates = dataframe.index[dataframe["Date"].duplicated(keep=False) & dataframe["Date"].ne("")].tolist()
    add_error("Date", "Duplicate monthly Date values were found", duplicate_dates)

    year_values = pd.to_numeric(dataframe["Year"], errors="coerce")
    month_values = pd.to_numeric(dataframe["Month"], errors="coerce")
    add_error("Year", "Year must be numeric", dataframe.index[dataframe["Year"].ne("") & year_values.isna()].tolist())
    add_error("Month", "Month must be an integer between 1 and 12", dataframe.index[dataframe["Month"].ne("") & (month_values.isna() | (month_values < 1) | (month_values > 12) | (month_values % 1 != 0))].tolist())
    add_error("Year", "Year must match Date", dataframe.index[dates.notna() & year_values.notna() & year_values.ne(dates.dt.year)].tolist())
    add_error("Month", "Month must match Date", dataframe.index[dates.notna() & month_values.notna() & month_values.ne(dates.dt.month)].tolist())

    for column in NON_NEGATIVE_COLUMNS + ["GDP_Growth_Rate_Percent"]:
        values = pd.to_numeric(dataframe[column], errors="coerce")
        add_error(column, "Value must be numeric", dataframe.index[dataframe[column].ne("") & values.isna()].tolist())
        if column in NON_NEGATIVE_COLUMNS:
            add_error(column, "Value cannot be negative", dataframe.index[values.notna() & values.lt(0)].tolist())

    valid_dates = dates.dropna()
    summary = {
        "status": "success" if not errors else "validation_failed",
        "file_name": filename,
        "total_records": len(dataframe),
        "valid_records": len(dataframe) - len(invalid_rows),
        "invalid_records": len(invalid_rows),
        "duplicate_months": len(set(dataframe.loc[duplicate_dates, "Date"])),
        "missing_values": missing_values,
        "economic_period": None if valid_dates.empty else {"start": valid_dates.min().strftime("%Y-%m"), "end": valid_dates.max().strftime("%Y-%m")},
        "errors": errors,
    }
    return MacroValidationResult(dataframe, summary)


def indicator_rows_for_insert(dataframe: pd.DataFrame, upload_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in dataframe.to_dict(orient="records"):
        rows.append({
            "upload_id": upload_id,
            "indicator_month": record["Date"],
            "inflation_rate": float(record["Inflation_Rate_Percent"]),
            "unemployment_rate": float(record["Unemployment_Rate_Percent"]),
            "cost_of_living_index": float(record["CPI_Index"]),
            "cpi_index": float(record["CPI_Index"]),
            "policy_interest_rate_percent": float(record["Policy_Interest_Rate_Percent"]),
            "usd_lkr_exchange_rate": float(record["USD_LKR_Exchange_Rate"]),
            "gdp_growth_rate_percent": float(record["GDP_Growth_Rate_Percent"]),
            "raw_data": record,
        })
    return rows
