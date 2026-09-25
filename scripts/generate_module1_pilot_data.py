"""Generate reproducible, synthetic Module 1 pilot datasets.

The HR column design follows the supplied IBM attrition file. The macroeconomic
values are copied only for the selected six-month period from the supplied Sri
Lanka macroeconomic CSV.
"""

import argparse
import csv
import random
from datetime import date
from pathlib import Path


RANDOM_SEED = 20260902


def random_date(start_year: int, end_year: int) -> date:
    year = random.randint(start_year, end_year)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return date(year, month, day)


def observation_date_for_employee(employee_number: int) -> date:
    """Assign every pilot employee to one of the six macroeconomic months.

    Cycling through the months guarantees that January-June 2023 are all
    represented in every regenerated 100-employee pilot dataset.
    """
    month = ((employee_number - 1) % 6) + 1
    return date(2023, month, random.randint(1, 28))


def generate_hr_rows(count: int) -> list[dict[str, str | int]]:
    departments = {
        "Sales": ["Sales Executive", "Sales Representative"],
        "Research & Development": ["Research Scientist", "Laboratory Technician", "Healthcare Representative", "Manager"],
        "Human Resources": ["Human Resources", "Manager"],
    }
    education_fields = ["Life Sciences", "Medical", "Marketing", "Technical Degree", "Human Resources"]
    rows: list[dict[str, str | int]] = []

    for number in range(1, count + 1):
        department = random.choices(list(departments), weights=[58, 32, 10])[0]
        job_role = random.choice(departments[department])
        job_level = random.choices([1, 2, 3, 4, 5], weights=[34, 31, 20, 11, 4])[0]
        age = random.randint(22, 59)
        total_years = random.randint(1, max(2, age - 18))
        years_at_company = random.randint(0, min(total_years, 18))
        attrition = "Yes" if random.random() < 0.19 else "No"
        resignation_date = ""
        if attrition == "Yes":
            resignation_date = date(2023, random.randint(1, 6), random.randint(1, 28)).isoformat()

        monthly_income = int((16000 + job_level * 23000 + years_at_company * 1900) * random.uniform(0.82, 1.18))
        rows.append({
            "EmployeeID": f"PILOT-{number:04d}",
            "Age": age,
            "Gender": random.choice(["Female", "Male"]),
            "Department": department,
            "JobRole": job_role,
            "JobLevel": job_level,
            "MonthlyIncome": monthly_income,
            "BusinessTravel": random.choices(["Non-Travel", "Travel_Rarely", "Travel_Frequently"], weights=[12, 64, 24])[0],
            "DistanceFromHome": random.randint(1, 29),
            "EducationField": random.choice(education_fields),
            "MaritalStatus": random.choice(["Single", "Married", "Divorced"]),
            "OverTime": random.choices(["Yes", "No"], weights=[28, 72])[0],
            "JobSatisfaction": random.randint(1, 4),
            "EnvironmentSatisfaction": random.randint(1, 4),
            "WorkLifeBalance": random.choices([1, 2, 3, 4], weights=[7, 23, 55, 15])[0],
            "TotalWorkingYears": total_years,
            "YearsAtCompany": years_at_company,
            "JoinDate": random_date(2013, 2022).isoformat(),
            "ResignationDate": resignation_date,
            "ObservationDate": observation_date_for_employee(number).isoformat(),
            "Attrition": attrition,
        })
    return rows


def select_macro_rows(source: Path) -> list[dict[str, str]]:
    with source.open(newline="", encoding="utf-8-sig") as source_file:
        rows = list(csv.DictReader(source_file))
    selected = [row for row in rows if "2023-01-01" <= row["Date"] <= "2023-06-01"]
    if len(selected) != 6:
        raise ValueError("The macroeconomic source must contain January through June 2023.")
    return selected


def write_csv(path: Path, rows: list[dict[str, str | int]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--macro-source", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("pilot-data"))
    arguments = parser.parse_args()

    random.seed(RANDOM_SEED)
    write_csv(arguments.output_dir / "module1_hr_pilot_100_employees.csv", generate_hr_rows(100))
    write_csv(arguments.output_dir / "module1_sri_lanka_macro_pilot_6_months.csv", select_macro_rows(arguments.macro_source))


if __name__ == "__main__":
    main()
