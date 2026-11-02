# Formula D: Real-Wage Economic Exposure Index

Status: proposed, unvalidated research candidate. A software correctness test does
not validate the index scientifically. Its 0–100 output is not a validated
psychological financial stress scale or a turnover probability.

## Definition and units

- `employee_wage`: nominal monthly employee wage in LKR, nonnegative.
- `ncpi`: National Consumer Price Index **2013=100**, positive.
- `reference_income_2013`: positive monthly income in **2013 purchasing-power
  LKR**. This is a different parameter from the nominal reference salary in A/B/C.
- `unemployment_rate`: national unemployment percentage, nonnegative.
- `alpha`: wage-gap weight in [0,1], default 0.5.

```
real_wage = employee_wage * 100 / ncpi
wage_gap = clip((reference_income_2013 - real_wage) / reference_income_2013, 0, 1)
normalized_unemployment = clip((unemployment_rate - 4.5) / (5.1 - 4.5), 0, 1)
score = 100 * (alpha * wage_gap + (1 - alpha) * normalized_unemployment)
```

Calculations retain precision; displayed scores use two decimal places.
All numeric inputs must be finite. Missing required inputs are rejected, never
imputed with zero. Zero wages are permitted. Derived real wages that cannot be
represented as finite floats are rejected explicitly.

## Threshold provenance and assumptions

There is **no default reference income**, including no implicit LKR 50,000.
Without one, the comparison returns `enabled=false` and an explanatory message;
the scenario endpoint rejects a missing threshold. The dashboard provides
session-only reference income, alpha, source and justification controls.
Changing these controls invalidates the previous results until reapplied.

No defensible threshold benchmark is established by this implementation. Every
threshold remains labeled **illustrative**, even when a user supplies provenance.
Source and justification are exported verbatim; empty fields mean not provided,
not verified. Future research must establish the threshold's population, period,
units, source and justification before treating it as a defensible benchmark.

The 4.5–5.1 unemployment interval is the user-specified **HIES 2019 demonstration
profile**, kept in its own constant and identified in every result. It is not a
universal normalization range. The API rejects other normalization profiles and
CPI base years. In particular, LFS 2024 NCPI 2021=100 is not supported here.
The HIES dataset's existing previous-calendar-month economic mapping is retained,
including December 2018 for January 2019 interviews; this is an alignment
assumption, not a change to the normalization profile.

The equal weighting is illustrative. Both normalized components are bounded;
clipping means further changes can stop affecting scores. Wage gaps vanish at or
above the threshold. Alpha=0 removes wage exposure, and alpha=1 removes
unemployment exposure. Household expenses, loans, debt, allowances and inflation
are not direct Formula D inputs.

## Integration and reproducibility

Existing A/B/C services, reference salaries, normalization profiles, model
contracts and prediction pipelines remain unchanged. D is an additional HIES
dashboard candidate with its own breakdown, sample comparison and scenario form.
It is not automatically selected as a turnover model feature or retrained model.

- `POST /api/v1/eesi/hies/formula-d`: optional configuration; returns enabled
  status, assumptions, configuration and per-person results.
- `POST /api/v1/eesi/formula-d/scenario`: required wage, NCPI, unemployment and
  reference income; alpha defaults to 0.5. Returns inputs, components,
  contributions, score and metadata.
- `POST /api/v1/eesi/hies/formula-d/export`: same configuration as comparison;
  downloads JSON with identical results and provenance.
- The dashboard's existing **Download calculation evidence** includes the A/B/C
  dataset, Formula D comparison/configuration, and current D scenario inputs and
  result. Draft scenario edits invalidate the old result.

Example request fields (supply your own justified threshold; none is assumed):
`reference_income_2013`, `alpha`, `reference_income_source`,
`reference_income_justification`, `cpi_base_year=2013`,
`normalization_profile="hies2019"`. Scenario requests additionally require
`employee_wage`, `ncpi`, `unemployment_rate`.

## Verification

From `backend`, run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_eesi_formula_d.py tests/test_eesi.py tests/test_hies_data.py tests/test_eesi_real.py -q
```

Tests cover exact values, monotonicity, thresholds, clipping, alpha endpoints,
score bounds, finite-number validation, missing values, incompatible CPI bases,
scenario/export parity, disabled configuration, recorded provenance and A/B/C
regression behavior. These tests establish software behavior only.

From `frontend`, run `npm.cmd run build` for TypeScript and production compilation.
Browser interaction is not covered by these backend tests.
