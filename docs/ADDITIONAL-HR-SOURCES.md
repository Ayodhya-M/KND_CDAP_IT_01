# Additional Module 1 source

Only the supplied Sri Lanka synthetic workbook is enabled. The imported IBM
benchmark and its dedicated model were removed at the user's request. The
importer no longer accepts an archive argument or enables a benchmark profile.
The original file in Downloads is untouched.

Open **Data Management > Additional sources**. The same source is accessible in
**Economic Intelligence > Additional imported sources** and the collapsed
additional-data sections in prediction and retention. Private local storage is
separate from the existing Supabase pilot and HIES sample; neither is modified.

## Data and meanings

All 50 rows on the workbook's `50 Synthetic Records` sheet are retained. The
Read Me labels them AI-generated examples, not genuine employee responses.
2019 months are scenario labels, not verified survey collection dates. The target
is intention to leave within 12 months, not observed attrition.

Relevant fields: age, department, categorical job level, fractional tenure,
monthly base salary, allowances, annual bonus, household expenses, debt payments,
overtime hours, self-rated performance (1-5), promotions in the last three years,
satisfaction (1-5), scenario month and intention target. IDs are replaced with
source-specific sample IDs. Gender, district, questionnaire text and unused
survey answers are excluded. Financial-worry and retention-preference answers
are not model predictors. The original workbook is never modified.

## Pipeline

The scenario month selects matching historical 2019 national NCPI, inflation
and quarterly unemployment; no random years are assigned. This is explicitly
a synthetic historical scenario, not real employee-level temporal validation.
The existing three EESI candidates use base salary and the frozen historical
economic reference ranges. Expenses, allowances, bonus and debt remain supporting
inputs and do not enter those formulas.

A separate intention classifier consumes HR attributes and additive EESI.
Preprocessing is fitted on 40 training records; 10 are held out. Target meanings,
1-5 scales and fractional tenure are preserved. The old pilot model is not
overwritten. Prototype suggestions use positive model-probability differences
under temporary salary, satisfaction or overtime probes. Salary probes also
recalculate EESI. Results are not SHAP, causal effects, validated employee-risk
bands or research performance claims. No supported sensitivity means no fabricated
suggestion. Scenarios do not modify stored records or model artifacts.

## Reimport

```powershell
.\backend\.venv\Scripts\python.exe scripts/import_additional_hr.py --workbook 'C:\Users\mitho\Downloads\Sri_Lanka_HR_50_SYNTHETIC_and_Survey.xlsx'
```

Content fingerprints reuse existing imports. Data and backups stay under
Git-ignored `data/private/`; source-specific models stay under
`artifacts/imported_sources/`. The active store is
`data/private/module1_sources.sqlite3`.
