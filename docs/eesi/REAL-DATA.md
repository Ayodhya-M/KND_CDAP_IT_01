# LFS 2024 EESI demonstration

The frontend's **EESI prototype** now opens the **Real Sri Lankan data** view by default. The synthetic pilot remains available for worked examples. Real survey microdata is held locally in `data/private/lfs2024/`, which is excluded from Git. The public API serves aggregate JSON only. Do not publish or share raw/processed microdata outside the DCS terms.

## Dataset and selected cohort

Source: user-supplied `LFS-2024-25-Percent-Data-Without-Computer.csv`, corresponding to DCS Labour Force Survey 2024. The file contains 17,771 respondents and 128 columns. Survey interview months run January-December 2024.

Eligibility: AGE >= 15, Q45 = 1 (main-job employee), positive finite Q45_A_1 (monthly gross salary), positive finite AnnualFactor_25Percent, valid 2024 interview month and matching economic inputs. Whitespace blanks are missing, not zero. Zero salary is excluded; daily wages and self-employment income are not substituted. No salary values are imputed or winsorized.

| Preparation result | Respondents |
| --- | ---: |
| Original source | 17,771 |
| Outside survey working age | 3,393 |
| Not a main-job employee, among age-eligible respondents | 10,598 |
| No monthly gross salary (including daily-wage branch) | 1,461 |
| Nonpositive monthly gross salary | 15 |
| Eligible monthly salaried employees | 2,304 |

Reasons are mutually exclusive in the order of the eligibility checks. Excluded records are largely outside the chosen cohort, not necessarily invalid survey responses. Other employee types can be considered separately later after defining equivalent income measures.

Q45(a)(i), questionnaire PDF page 15, defines last month's gross salary including allowances. Q45(a)(ii) additional earnings, Q45(a)(iii) income in kind, secondary employment, daily wages and self-employment income are omitted. Q57 is expected income of job seekers and is not employee salary. These distinctions matter when explaining the exposure variable.

## Economic period alignment

The implementation assumes YEAR/MONTH identifies the interview month and interprets "last month" as the preceding calendar month. January 2024 interviews therefore use December 2023 income conditions; December interviews use November 2024 conditions. This is an explicit approximation: exact interview dates and an explicit microdata reference-period code are not provided. Confirm this interpretation with DCS before final research.

Economic values are transcribed into `data/reference/eesi/economic-reference.csv` from the official source tables after PDF visual inspection:

- **National headline NCPI**, base 2021=100, and its **year-on-year inflation** from the DCS NCPI movements table (PDF page 1).
- **National quarterly unemployment**, total row in Selected Labour Force Indicators, LFS 2024 Q4 report (PDF page 8). Q4 2023: 4.3%; Q1 2024: 4.5%; Q2: 4.7%; Q3: 4.2%; Q4: 4.2%.

The quarter containing the income month supplies unemployment for each month in that quarter. No monthly unemployment series is invented or interpolated. This is a retrospective descriptive experiment using subsequently published statistics, not a claim that all indicators were available on the interview date.

Official sources:

- [Dataset provenance and usage conditions](https://nada.statistics.gov.lk/index.php/catalog/490/study-description)
- [2024 questionnaire](https://nada.statistics.gov.lk/index.php/catalog/490/download/4578)
- [NCPI index and inflation movements](https://www.statistics.gov.lk/Resource/en/InflationAndPrices/NCPI/MovementsofNCPIandNCPI-Core.pdf)
- [LFS 2024 Q4 report](https://www.statistics.gov.lk/Resource/en/LabourForce/Quarterly_Reports/2024Q4report.pdf)

Required source attribution: Department of Census and Statistics, Sri Lanka Labour Force Survey - 2024, Version 1.0 of the public use dataset, provided by the National Data Archive, Data Processing Division, www.statistics.gov.lk.

## Calculation and aggregate reporting

Version `pp1-lfs2024-v1` retains the three candidate formula structures documented in PP1-GUIDE.md. Frozen reference ranges from the twelve income months are inflation -1.7 to 6.5%, NCPI 202.1 to 215.0, and unemployment 4.2 to 4.7%. Normalize with clipped min-max scaling. Deflation is allowed as a raw input; zero normalized inflation means the reference minimum, not zero economic hardship. The salary exposure reference remains an illustrative LKR 50,000 per month.

The pilot's CPI proxy scale and 2023 bounds are not reused. Real-data scores and synthetic-pilot scores are **not comparable**, even though they both use 0-100 displays. The narrow economic reference window remains a limitation requiring sensitivity analysis.

Outputs include unweighted sample means and descriptive weighted means using AnnualFactor_25Percent. Weighted mean = sum(weight * score) / sum(weight). This is not a calibrated estimate for all Sri Lankan employees: the selected cohort excludes daily earners and salary-incomplete records. No population total, confidence interval, or accuracy percentage is reported.

The API exposes overall summaries, twelve income-month groups and five broad salary bands. Every actual displayed group has at least 162 respondents. No respondent identifiers, household keys, demographics, exact salaries or individual score records are exposed. Monthly respondents differ, so month-to-month variation is not a longitudinal stress trajectory. Salary groups have different month compositions; their observed differences are not causal evidence.

Small-group suppression below 30 is a basic guard, not a complete statistical disclosure-control system. New grouping schemes require review for complementary disclosure before sharing.

## Reproduce locally

```powershell
python scripts/prepare_lfs2024.py
```

Or supply the source path explicitly:

```powershell
python scripts/prepare_lfs2024.py --source "C:\Users\mitho\Downloads\LFS-2024-25-Percent-Data-Without-Computer.csv"
```

The script writes a minimal private intermediate and `docs/eesi/lfs2024-aggregate.json`. SHA-256 hashes of the source and economic CSV identify the exact inputs without redistributing respondent data. The aggregate file lets the demo operate without private records on the server. Reproduction needs the user's authorized local survey copy. No raw data needs to enter Supabase.

GET `/api/v1/eesi/real-data` reads aggregates. POST `/api/v1/eesi/scenario` accepts `reference_profile: "lfs2024"` to calculate hypothetical salaries under the real-data normalization. Omitting the profile preserves the synthetic pilot scenario behaviour.

## PP1 claims and remaining work

Supported: real salary inputs, official matched macroeconomic indicators, transparent candidate formulas, reproducible calculations, tested preparation, aggregate comparisons, and independence from Module 1 completion.

Not established: financial-stress accuracy, superiority of one candidate, population representativeness of the selected cohort, a causal salary effect, or improved turnover prediction. The LFS source does not provide an independently verified stress target for these calculations. Continue independent survey validation, reference-window and weight sensitivity, inflation/CPI ablation, held-out evaluation, and final formula selection after PP1.

For the presentation, show the cohort count, economic input table, candidate group means and a controlled salary scenario. State the income timing assumption and quarterly unemployment mapping. Use synthetic examples to explain individual arithmetic, keeping real respondent outputs aggregate-only.
