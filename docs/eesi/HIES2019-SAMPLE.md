# HIES 2019 financial sample

The private sample is stored in `data/private/hies2019_100/`, which is excluded
from Git by the existing `data/private/` rule. Do not publish these microdata.

## Contents

- `wage_earners_100.csv`: exactly 100 adult positive-wage recipients from 100
  distinct households, with generated sample IDs, survey year/month, reported
  wages, allowances, bonuses, income primary/secondary code, and ten reported
  household debt amount fields. No original household/person identifiers,
  location codes, age, ethnicity, religion, or health information are exported.
- `household_expenses.csv`: food and nonfood item codes, reported values and
  in-kind values for only those 100 households. `SampleID` links to the sample.
  Multiple expense lines belong to each household; these are not extra employees.
- `manifest.json`: source checksum, selection method, counts and limitations.

## Interpretation

This is a reproducible exploratory sample of wage recipients, not a
representative national estimate or an organizational HR dataset. Only unique
person income matches with an adult demographic match are eligible. Selection
uses seed 2019 and one person per household. It excludes people with multiple
income records instead of arbitrarily choosing a primary or secondary record.

Income fields preserve source amounts. Blank allowances, bonuses and debts
remain missing, never automatically zero. The source spelling `allowences` is
mapped to `AllowancesReported`. Ten household debt amount fields retain their
source names with `Household_` and `_reported` added.

Household expenses and debts must not be relabeled as the employee's personal
expenses or personal loans. No debt amount is assumed to be a monthly repayment.
Food and nonfood reporting periods can differ. Verify questionnaire definitions,
item codes, currency/units, period conversions, debt semantics and missing-value
codes before deriving monthly totals, disposable income or EESI. The extraction
does not calculate any such totals or scores.

The 2019 survey month is preserved. Do not match these observations to the
existing 2023 macro pilot or 2024 LFS data as contemporaneous observations.
Tenure, performance, job satisfaction, promotions and attrition are not supplied
by this extraction and have not been invented. Do not join these respondents to
the synthetic PILOT employees by row order or generated sample ID.

The existing HR pilot, HR upload validation and Supabase records are unchanged.
These CSVs are not compatible with the organizational HR upload contract.
The app now provides a separate private local HIES import as described below.

## Cleaned PP1 files

Run `python scripts/clean_hies2019_eesi.py` after extraction. It produces:

- `eesi_inputs_100_clean.csv`: 100 validated records with typed numeric amounts,
  monthly equivalents, economic context, missingness and quality flags.
- `expenses_monthly_audit.csv`: the same 8,143 selected expense lines with source
  reporting periods and conversion factors for checking the monthly equivalents.
- `eesi_existing_candidates_100.csv`: all 100 records calculated using the three
  existing salary-and-economy candidates. These do **not** include household
  expenditure, allowances, bonus or debt in the score. The financial fields in
  the clean file are supporting inputs for later formula development.
- `cleaning_report.json`: counts, definitions, conversion choices and missing
  input totals. No raw source join keys are included.

The earlier interpretation cautions above describe the raw extraction. The
following questionnaire definitions have now been checked:

| Field | Definition and processing |
| --- | --- |
| Wages | Employee wages/salaries in last calendar month or last four weeks. Retained as reported. |
| Extra employment pay | Source `allowences` corresponds to tips, commissions and overtime etc. on the questionnaire. This is not a verified fixed allowance field. |
| Bonus | Bonus and arrears over last 12 calendar months. Divide by 12 for monthly equivalent, not actual payment that month. |
| Food | Weekly household consumption. Multiply by 52/12 as an explicit monthly-equivalent convention. |
| Nonfood | Monthly/monthly-average items unchanged. Clothing, footwear and small durable categories 30-32 divided by 6. Category 33 durable purchases divided by 12, except installment/leasing codes 3341/3342 retained monthly. |
| Annual exceptions | Transport license/insurance codes 2421/2422, education codes 2609-2613, and category 35 divided by 12. |
| Debt payments | Household nonfood code 3405, including interest, last month. Recorded for 41 selected households. Unreported payments remain missing, not zero. |
| Outstanding debt | Section 6B amount to pay is a stock. Missing lender amounts prevent a complete total. Known amounts are retained separately; not treated as monthly repayments. |
| In-kind values | Retained separately in the audit. Not added again to reported expenditure. Blank in-kind fields remain missing. Expenditure totals are reported consumption/expenditure values, not verified out-of-pocket cash spending. |

All amounts are in Sri Lankan rupees. Total recorded expenditure includes broad
survey categories such as savings, transfers, property purchases and debt
payments. It must not be labeled essential living costs. Debt payments are
already inside nonfood expenditure and must not be added again. Rent code 2001
can include estimated owner-occupied housing rent, so the total is not disposable
cash expenditure. A personal budget cannot be calculated by subtracting the full
household total from one employee's salary.

### Economic alignment and candidate calculations

`data/reference/eesi/hies2019-economic-reference.csv` contains national NCPI
(2013=100), headline year-on-year inflation and quarterly national unemployment.
For PP1, the previous calendar month is used as an **explicit assumption** for
income reference. The questionnaire also permits last four weeks, so precise
income dates cannot be recovered. January 2019 survey records map to December
2018. Annual and six-month expenses remain monthly averages over their source
windows; assigning context does not make them observations of only that month.
Quarterly unemployment is repeated across its three months without interpolation.
This is a retrospective demonstration and does not enforce publication-time
availability for forecasting.

Candidate version `hies2019-pp1-inputs-v1` uses the existing economic, additive and
interaction formula definitions from `backend/app/services/eesi.py`. Frozen
reference bounds cover December 2018-December 2019: inflation 0.4-6.2%, NCPI
126.4-135.0, unemployment 4.5-5.1%. The existing illustrative salary reference of
LKR 50,000 is retained, not an official living wage. These are exploratory
comparators, not validated employee stress measurements. Their separate bounds
must be used when reproducing these scores; the current scenario API's pilot and
LFS profiles use different reference ranges and must not be substituted.

### Completeness for the presentation

All 100 records have positive wages, expense data and economic matches. Only
5 have all wage, extra-pay and bonus fields recorded. Extra pay is missing for
85; bonuses for 91; debt payments are recorded for 41. No missing financial
values are imputed. `FinalEESIReady` is false because a complete personal-finance
formula, personal cost allocation and missing inputs are not available. This does
not prevent calculating the existing wage-and-economy candidate indices.

Suggested presentation statement:

> Prepared 100 adult wage-recipient records from HIES 2019, standardized household
> expenditure reporting periods, separated debt payments from outstanding debt,
> and aligned economic context. Calculated three exploratory wage-and-economy
> EESI candidates. Additional financial inputs and missingness are documented for
> future development of the financial EESI formula.

Definitions checked against the DCS HIES 2019 questionnaire, printed pages 9-20,
22 and 28: https://catalog.ihsn.org/catalog/11323/download/101089

NCPI and inflation: CBSL publication reproducing DCS values, Table 1, PDF page 2:
https://www.cbsl.gov.lk/sites/default/files/cbslweb_documents/press/pr/press_20211021_inflation_in_september_2021_ncpi_e.pdf

December 2018 NCPI/inflation: DCS historical table:
https://www.statistics.gov.lk/Resource/en/InflationAndPrices/NCPI/Inflation-FoodAndNonFoodGroups-2013.pdf

Unemployment, including 2018Q4: DCS 2019Q4 report, selected indicators, PDF page 7:
https://www.statistics.gov.lk/Resource/en/LabourForce/Quarterly_Reports/2019Q4report.pdf

## Reproduce

```powershell
python scripts/prepare_hies2019_sample.py --source 'C:\Users\mitho\Downloads\HIES-2019-25%.zip'
```

The ZIP is read in place; the full archive is not extracted. Original join keys
are used only in memory, and no identifying crosswalk is written.

Source dictionary: https://nada.statistics.gov.lk/index.php/catalog/476/data-dictionary

## App import and display

The backend stores the imported prepared sample in the Git-ignored local
`data/private/hies2019_app.sqlite3` database. The overview shows a separate
**HIES wage earners** count. **Economic Intelligence > HIES 2019** displays the
financial records and candidate calculations. Use **Import prepared 100-person
sample** or **Reimport prepared sample** to import the fixed prepared CSV.
Reimport replaces this local sample atomically instead of duplicating records.

API routes: `GET /api/v1/eesi/hies` and
`POST /api/v1/eesi/hies/import-prepared`. Validation requires exactly 100 unique
sample IDs, finite amounts and matching historical months. Missing financial
values stay null and are displayed as **Not reported**. Candidate calculations
reuse the same formulas and historical bounds documented above.

This import does not create organizational HR records, change Supabase, train
Module 3 or enable real Module 4 recommendations. Database connection failures
are displayed as **Unavailable**, rather than an empty HR record count.
Configure real `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` values in
`backend/.env` and restart the backend to enable the organizational HR workflow.
Keep credentials on the backend; do not add service-role keys to frontend files.
