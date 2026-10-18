from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import Any

import pandas as pd


REQUIRED_COLUMNS = [
    "EmployeeID", "Age", "Gender", "Department", "JobRole", "JobLevel",
    "MonthlyIncome", "BusinessTravel", "DistanceFromHome", "EducationField",
    "MaritalStatus", "OverTime", "JobSatisfaction", "EnvironmentSatisfaction",
    "WorkLifeBalance", "TotalWorkingYears", "YearsAtCompany", "JoinDate",
    "ObservationDate", "Attrition",
]
PILOT_START = pd.Timestamp("2023-01-01")
PILOT_END = pd.Timestamp("2023-06-30")

NUMERIC_RULES = {
    "Age": (14, 100),
    "JobLevel": (1, 5),
    "MonthlyIncome": (0, None),
    "DistanceFromHome": (0, None),
    "JobSatisfaction": (1, 4),
    "EnvironmentSatisfaction": (1, 4),
    "WorkLifeBalance": (1, 4),
    "TotalWorkingYears": (0, None),
    "YearsAtCompany": (0, None),
}


@dataclass
class HRValidationResult:
    dataframe: pd.DataFrame | None
    summary: dict[str, Any]

    @property
    def is_valid(self) -> bool:
        return self.dataframe is not None and self.summary["invalid_records"] == 0


def _sample_rows(indexes: list[int]) -> list[int]:
    return [index + 2 for index in indexes[:10]]


def validate_hr_csv(content: bytes, filename: str) -> HRValidationResult:
    if not content.strip():
        return HRValidationResult(None, {"status": "validation_failed", "file_name": filename, "errors": [{"field": "file", "message": "CSV file is empty"}]})

    try:
        dataframe = pd.read_csv(BytesIO(content), dtype=str, keep_default_na=False)
    except pd.errors.EmptyDataError:
        return HRValidationResult(None, {"status": "validation_failed", "file_name": filename, "errors": [{"field": "file", "message": "CSV file is empty"}]})
    except Exception as error:
        return HRValidationResult(None, {"status": "validation_failed", "file_name": filename, "errors": [{"field": "file", "message": f"CSV could not be read: {error}"}]})

    dataframe.columns = [str(column).strip() for column in dataframe.columns]
    dataframe = dataframe.map(lambda value: value.strip() if isinstance(value, str) else value)
    if dataframe.empty:
        return HRValidationResult(None, {"status": "validation_failed", "file_name": filename, "errors": [{"field": "file", "message": "CSV contains headers but no employee records"}]})

    missing_columns = [column for column in REQUIRED_COLUMNS if column not in dataframe.columns]
    if missing_columns:
        return HRValidationResult(None, {
            "status": "validation_failed",
            "file_name": filename,
            "total_records": len(dataframe),
            "errors": [{"field": "columns", "message": "Required columns are missing", "columns": missing_columns}],
        })

    errors: list[dict[str, Any]] = []
    invalid_rows: set[int] = set()

    def add_error(field: str, message: str, indexes: list[int]) -> None:
        if not indexes:
            return
        invalid_rows.update(indexes)
        errors.append({"field": field, "message": message, "count": len(indexes), "sample_rows": _sample_rows(indexes)})

    missing_values: dict[str, int] = {}
    for column in dataframe.columns:
        missing_indexes = dataframe.index[dataframe[column].eq("")].tolist()
        if missing_indexes:
            missing_values[column] = len(missing_indexes)
            if column in REQUIRED_COLUMNS:
                add_error(column, "Required value is missing", missing_indexes)

    duplicate_mask = dataframe["EmployeeID"].duplicated(keep=False) & dataframe["EmployeeID"].ne("")
    duplicate_indexes = dataframe.index[duplicate_mask].tolist()
    duplicate_employee_ids = sorted(dataframe.loc[duplicate_mask, "EmployeeID"].unique().tolist())
    add_error("EmployeeID", "Duplicate EmployeeID values were found", duplicate_indexes)

    parsed_observation = pd.to_datetime(dataframe["ObservationDate"], format="%Y-%m-%d", errors="coerce")
    invalid_observation = dataframe.index[dataframe["ObservationDate"].ne("") & parsed_observation.isna()].tolist()
    add_error("ObservationDate", "ObservationDate must use YYYY-MM-DD", invalid_observation)
    out_of_period = dataframe.index[parsed_observation.notna() & ((parsed_observation < PILOT_START) | (parsed_observation > PILOT_END))].tolist()
    add_error("ObservationDate", "ObservationDate must be between 2023-01-01 and 2023-06-30", out_of_period)

    parsed_join = pd.to_datetime(dataframe["JoinDate"], format="%Y-%m-%d", errors="coerce")
    add_error("JoinDate", "JoinDate must use YYYY-MM-DD", dataframe.index[dataframe["JoinDate"].ne("") & parsed_join.isna()].tolist())
    if "ResignationDate" in dataframe.columns:
        parsed_resignation = pd.to_datetime(dataframe["ResignationDate"], format="%Y-%m-%d", errors="coerce")
        add_error("ResignationDate", "ResignationDate must use YYYY-MM-DD when supplied", dataframe.index[dataframe["ResignationDate"].ne("") & parsed_resignation.isna()].tolist())
        chronology_error = dataframe.index[parsed_join.notna() & parsed_resignation.notna() & (parsed_resignation < parsed_join)].tolist()
        add_error("ResignationDate", "ResignationDate cannot be earlier than JoinDate", chronology_error)

    for column, (minimum, maximum) in NUMERIC_RULES.items():
        values = pd.to_numeric(dataframe[column], errors="coerce")
        invalid_numeric = dataframe.index[dataframe[column].ne("") & values.isna()].tolist()
        add_error(column, "Value must be numeric", invalid_numeric)
        out_of_range_mask = values.notna() & (values < minimum)
        if maximum is not None:
            out_of_range_mask |= values > maximum
        add_error(column, f"Value must be between {minimum} and {maximum if maximum is not None else 'unlimited'}", dataframe.index[out_of_range_mask].tolist())

    invalid_attrition = dataframe.index[dataframe["Attrition"].ne("") & ~dataframe["Attrition"].isin(["Yes", "No"])].tolist()
    add_error("Attrition", "Attrition must be Yes or No", invalid_attrition)
    invalid_overtime = dataframe.index[dataframe["OverTime"].ne("") & ~dataframe["OverTime"].isin(["Yes", "No"])].tolist()
    add_error("OverTime", "OverTime must be Yes or No", invalid_overtime)

    valid_observation = parsed_observation.dropna()
    period = None if valid_observation.empty else {"start": valid_observation.min().strftime("%Y-%m"), "end": valid_observation.max().strftime("%Y-%m")}
    summary = {
        "status": "success" if not errors else "validation_failed",
        "file_name": filename,
        "total_records": len(dataframe),
        "valid_records": len(dataframe) - len(invalid_rows),
        "invalid_records": len(invalid_rows),
        "duplicate_employee_ids": len(duplicate_employee_ids),
        "duplicate_employee_id_values": duplicate_employee_ids,
        "missing_values": missing_values,
        "observation_period": period,
        "errors": errors,
    }
    return HRValidationResult(dataframe, summary)


def employee_rows_for_insert(dataframe: pd.DataFrame, upload_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in dataframe.to_dict(orient="records"):
        rows.append({
            "upload_id": upload_id,
            "employee_id": record["EmployeeID"],
            "age": int(record["Age"]),
            "salary": float(record["MonthlyIncome"]),
            "department": record["Department"],
            "join_date": record["JoinDate"],
            "resignation_date": record.get("ResignationDate") or None,
            "observation_date": record["ObservationDate"],
            "attrition": record["Attrition"] == "Yes",
            "gender": record["Gender"],
            "job_role": record["JobRole"],
            "job_level": int(record["JobLevel"]),
            "business_travel": record["BusinessTravel"],
            "distance_from_home": int(record["DistanceFromHome"]),
            "education_field": record["EducationField"],
            "marital_status": record["MaritalStatus"],
            "overtime": record["OverTime"] == "Yes",
            "job_satisfaction": int(record["JobSatisfaction"]),
            "environment_satisfaction": int(record["EnvironmentSatisfaction"]),
            "work_life_balance": int(record["WorkLifeBalance"]),
            "total_working_years": int(record["TotalWorkingYears"]),
            "years_at_company": int(record["YearsAtCompany"]),
            "raw_data": record,
        })
    return rows
