# Module 1 pilot data

This folder contains reproducible demo data for the HR & Macroeconomic Data Integration module.

- `module1_hr_pilot_100_employees.csv`: 100 synthetic employee records.
- `module1_sri_lanka_macro_pilot_6_months.csv`: January-June 2023 Sri Lanka macroeconomic indicators, selected from the provided source file.

The HR dataset is synthetic. Its attribute design follows the supplied IBM employee-attrition dataset; it does not copy individual employee records.

## Upload column mapping

| CSV field | Database field |
| --- | --- |
| `EmployeeID` | `employee_records.employee_id` |
| `MonthlyIncome` | `employee_records.salary` |
| `JoinDate`, `ResignationDate` | `employee_records.join_date`, `resignation_date` |
| `Attrition` (`Yes`/`No`) | `employee_records.attrition` (`true`/`false`) |
| `Date` | `economic_indicators.indicator_month` |
| `Inflation_Rate_Percent` | `economic_indicators.inflation_rate` |
| `Unemployment_Rate_Percent` | `economic_indicators.unemployment_rate` |
| `CPI_Index` | `economic_indicators.cpi_index` and cost-of-living proxy |

## Regenerate data

```powershell
python scripts/generate_module1_pilot_data.py `
  --macro-source "C:\Users\USER\Downloads\sample_sri_lanka_macroeconomic_data_pilot.csv"
```
