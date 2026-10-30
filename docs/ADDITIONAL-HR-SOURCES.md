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

## Experimental Financial Burden Adjustment

In **Economic Intelligence > Additional imported sources**, select the Sri Lanka
50-record source and an employee. Turn **Display experimental adjustment** ON.
The section starts OFF and is also available in the full additional-source view.
Formula B is the main original score; the table compares separate experimental
adjustments with available original A/B/C scores. Formula D is not implemented
for this source. The toggle only controls display.

Exact column mappings and equations:

- `T = Monthly_Base_Salary_LKR + Monthly_Allowances_LKR`
- `M = Monthly_Household_Expenses_LKR + Monthly_Debt_Payments_LKR`
- `F = min(1, M / T)`, only when `T > 0`
- `Adjusted_EESI = 0.70 * Original_EESI + 0.30 * (100 * F)`
- `Difference = Adjusted_EESI - Original_EESI` (score points)
- `Annual_Bonus_LKR` is retained but excluded from the calculation.
- `Survey_Month` continues to select the existing historical economic context;
  the adjustment introduces no new normalization or date mapping.

**Explicit synthetic-data assumption authorized for this experiment:**
`Monthly_Household_Expenses_LKR` excludes `Monthly_Debt_Payments_LKR`.
The workbook does not verify this exclusion. It is not a verified fact about
real employee spending. Household commitments are compared with one employee's
income; other household income is not measured here. Base salary is before
deductions, so total monthly income is not a verified take-home income measure.

Missing, boolean, negative, nonnumeric, nonfinite or overflowing financial values
produce an unavailable adjustment, never zero imputation. Zero total income is
unavailable. Existing import validation still rejects invalid required values.
The additive API field `financial_burden_adjustment` is computed read-only after
prediction; it does not change stored records, formula outputs, model artifacts,
prediction features, recommendations, or scenario behavior.

The panel displays this disclaimer:

> Experimental adjustment using synthetic pilot data.
> The 70/30 weighting is a preliminary research assumption.
> This score has not been validated against actual employee financial stress.

### PP1 demonstration

1. Open the source and select a record; show original A/B/C scores.
2. Turn the experimental section ON. Identify salary, allowances, household
   expenses and debt; explain the synthetic exclusion assumption and bonus exclusion.
3. Show original B beside adjusted B and the signed point difference. Explain
   that adjustment can increase or decrease the score, depending on the burden.
4. Select another record and compare. A burden of 100% means commitments reach
   or exceed income; clipping hides how far above income they are.
5. Show the A/B/C comparison table. State that the original formulas are unchanged
   and prediction continues to consume original B.
6. Turn the section OFF to return to the existing display. Existing salary +10%
   scenario behavior is preserved; saved records remain unchanged.

Validation, from `backend/`:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_financial_burden.py tests/test_source_datasets.py tests/test_eesi.py tests/test_eesi_formula_d.py -q
```

From `frontend/`, run `npm.cmd run build`.

## Experimental B2/C2 extensions (50-record source only)

These are separate candidate formulas, **not the existing 70/30 adjustment**.
All original A/B/C calculations, normalizations and HIES Formula D remain
unchanged. Original B remains the prediction feature. The read-only response
adds `experimental_eesi`; it never updates the source records or model artifacts.
The selected employee view displays A, B, B2, C and C2 together, signed score
differences, financial inputs, raw economic inputs, normalized I/C/U/V, and
expandable point-contribution breakdowns. The earlier 70/30 panel remains separate.

The financial validation and variables are reused from `financial_burden.py`:

```text
T = Monthly_Base_Salary_LKR + Monthly_Allowances_LKR
M = Monthly_Household_Expenses_LKR + Monthly_Debt_Payments_LKR
F_raw = M / T                  (requires T > 0)
F = min(1, F_raw)
DSR = Monthly_Debt_Payments_LKR / T
B2 = 100 * (I + C + U + V + F) / 5
C2 = 100 * ((I + C + U) / 3) * ((V + F) / 2)
```

DSR is an uncapped descriptive ratio, not a further score input. Annual bonuses
are excluded. V still uses base salary S, not T: `V = R/(R+S)` with the existing
reference salary. Survey_Month retains its original historical economic mapping.
Raw/capped burden are displayed as ratios and percentages. Invalid, missing,
negative, boolean, nonfinite, overflowed, or zero-total-income inputs yield an
unavailable experiment rather than zero imputation. Existing import validation
remains unchanged. B2 assigns each component a 20% weight. C2 averages V and F
before multiplying the economic average; its displayed economic contributions
sum to the score.

### Conceptual foundations (official sources verified 30 October 2026)

- [CFPB: Measuring financial well-being](https://www.consumerfinance.gov/data-research/research-reports/financial-well-being-scale/)
  provides a separately researched questionnaire-based measure of financial
  security and freedom of choice. It motivates independent validation rather
  than treating income ratios alone as measured well-being.
- [CGAP: Measuring Financial Health: A Framework](https://www.cgap.org/research/publication/measuring-financial-health-framework)
  considers objective financial situations alongside subjective experience.
  This motivates exploring commitments relative to income, but the ratio here
  does not cover the full framework or constitute a CGAP score.
- [OECD: G20 policy note on financial well-being](https://www.oecd.org/en/publications/g20-policy-note-on-financial-well-being_7332c99d-en.html)
  provides a conceptual framework and working definition. Meeting financial
  commitments is conceptually relevant; this experiment measures only a narrow
  proposed exposure channel, not comprehensive financial well-being.
- [OECD/JRC: Handbook on Constructing Composite Indicators](https://www.oecd.org/en/publications/handbook-on-constructing-composite-indicators-methodology-and-user-guide_9789264043466-en.html)
  is a methodological foundation for examining normalization, weighting,
  aggregation and robustness of a composite index.

**B2/C2 are our proposed experimental equations. These references neither
provide these exact equations nor validate them.**

### Limitations and PP1 justification

Adding F tests whether commitments relative to income add a different exposure
channel to the original salary-and-economy index. B2 tests an additive structure;
C2 tests an interaction structure. Their numerical differences demonstrate
formula behavior, not improved accuracy.

- Equal weights are unvalidated. In B2, original components fall from 25% each
  to 20%; a changed score reflects that reweighting as well as the added F.
- CPI and inflation overlap; indicator ablation is needed.
- Salary appears in both V and F, potentially double-counting income exposure.
- Household expenses are compared with one individual's income, not all income
  of the household. Base salary is before deductions.
- Exclusion of debt from household expenses is an authorized synthetic-data
  assumption, not a verified real-spending definition.
- Capping hides variation above income: 29 of 50 records were capped in the
  inspected import. Show F_raw so this information remains visible.
- Synthetic data cannot validate real financial stress. Independent measures,
  sensitivity analysis and held-out real-data evaluation remain necessary.

### Worked imported record: SL-SYN-0001, 2019-03

Base salary 58,000; allowances 2,500; household expenses 101,000; debt 0 LKR.
T = 60,500; M = 101,000; F_raw = 1.669421 (166.94%); F = 1; DSR = 0.
Existing economic inputs: inflation 2.9%, NCPI 126.4, unemployment 4.7%.
Existing normalized components: I = 0.43103448, C = 0,
U = 0.33333333, V = 0.46296296.

| Score | Value / 100 | Difference from original |
| --- | ---: | ---: |
| A | 25.4789 | — |
| B | 30.6833 | — |
| B2 | 44.5466 | B2 − B = +13.8633 |
| C | 11.7958 | — |
| C2 | 18.6374 | C2 − C = +6.8416 |

For PP1, select this record under Additional imported sources, show the five
scores, explain the uncapped 166.94% versus capped 100%, then expand B2/C2 to
show contributions. Explain that the older 70/30 calculation is a separate
experiment and that prediction still consumes B = 30.6833. No reimport is needed.


## Four-family Module 2 organization

UI names now organize the unchanged calculation IDs under four families:

| Family | Basic | Extended experimental |
| --- | --- | --- |
| A ? Economic Baseline | 100*(I+C+U)/3 | None |
| B ? Additive Financial Exposure | 100*(I+C+U+V)/4 | 100*(I+C+U+V+F)/5 (legacy ID B2) |
| C ? Financial Interaction | 100*((I+C+U)/3)*V | 100*((I+C+U)/3)*((V+F)/2) (legacy ID C2) |
| D ? Real-Wage / Purchasing Power | Existing HIES implementation | None |

D retains RW=100*S/CPI and G=clip((Z-RW)/Z,0,1). Its existing alpha defaults
to 0.5, giving 100*(0.5G+0.5U). Configurable alpha remains unchanged; D is not
introduced to any other dataset. Z remains a configured reference real income.

| Dataset | Available family versions |
| --- | --- |
| HIES 2019 | A, Basic B/C, D after configuring Z; no financial extensions |
| LFS 2024 | A, Basic B/C only |
| Additional Sources: 50 synthetic records | A, Basic/Extended B and Basic/Extended C |
| 100-record pilot | A, Basic B/C; extended comparisons unavailable |
| 300-record pilot | A, Basic B/C; extended comparisons unavailable |

The pilot view now offers a 100/300 selector. The existing `/eesi/pilot` default
still returns the 100-record dataset; optional `?size=300` reads the existing
300-record file. Both datasets and normalization are unchanged. Their source
files do not contain household expense and debt fields. The 300-record file
also lacks allowances; the 100-record AdditionalIncome field is not assumed to
mean allowances. Same-employee Basic/Extended comparison rows show unavailable
extended values and differences rather than fabricating them. No missing
financial data or expense-exclusion assumption is supplied for either pilot.

The 50-record view now has one formula-family section, with original/extended
B and C grouped together and clear basic/extension versions. The duplicate
original-score section is removed. The 70/30 panel is retained under a collapsed
**Earlier experiment** section. Legacy API IDs B2/C2 remain compatible, while UI
names identify them as Extended B/C. Predictions continue consuming original B.
The existing verified conceptual references and research limitations above
apply; family grouping is not empirical validation.
