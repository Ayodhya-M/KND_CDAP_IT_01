# Module 2 to Module 3 Integration Contract — PP1

## Purpose and Status

This contract joins Module 1 HR features, one **explicitly selected** Module 2 EESI candidate, and Module 3 prediction. It is implemented for the repository's synthetic pilot data only. It demonstrates software integration; it does not validate EESI or turnover performance.

## Record Contract

| Field | Owner | Type | Module 3 use |
| --- | --- | --- | --- |
| `EmployeeID` | Module 1 | string | Traceability only; never a model feature |
| `ObservationMonth` | Module 1 | `YYYY-MM` string | Temporal provenance; never a model feature unless separately justified |
| `EESI` | Module 2 | finite number, 0–100 for PP1 candidates | Optional predictor feature |
| `EESIFormulaId` | Module 2 | `economic`, `additive`, or `interaction` | Required provenance metadata |
| `EESIFormulaVersion` | Module 2 | string | Required reproducibility metadata |
| `Attrition` | Module 1 | existing target label | Training/evaluation target only, never an input feature |

The pilot export also includes selected HR predictors: `Age`, `MonthlyIncome`, `OverTime`, `JobSatisfaction`, `JobLevel`, `YearsAtCompany`, and `Department`.

## API

- `GET /api/v1/module3/integration-contract` returns the machine-readable contract.
- `GET /api/v1/module3/pilot-export?formula_id=additive` returns a synthetic ML-ready CSV.
- `GET /api/v1/module3/prediction-status` reports whether a saved local model is available.
- `POST /api/v1/module3/predict` accepts a record matching the saved feature contract and returns a genuine saved-model prediction.
- `GET /api/v1/module3/evaluation` returns the saved held-out evaluation report.

The export rejects unsupported formula IDs and contains only one formula ID/version per file. It excludes unnecessary fields such as resignation dates. This endpoint intentionally does not read Supabase or expose real employee data.

## Module 3 Training Boundary

Download the pilot export only to demonstrate pipeline mechanics:

```powershell
Invoke-WebRequest http://localhost:8000/api/v1/module3/pilot-export?formula_id=additive -OutFile artifacts\module3_synthetic_pilot.csv

py -m module3_ml.cli train `
  --data artifacts\module3_synthetic_pilot.csv `
  --target Attrition `
  --features Age,MonthlyIncome,OverTime,JobSatisfaction,JobLevel,YearsAtCompany,Department,EESI `
  --eesi-column EESI `
  --artifact-dir artifacts\module3_synthetic
```

Any metrics generated from this export are **synthetic-pilot technical evidence only**, not research findings or evidence that EESI improves turnover prediction.

## Unified UI

Run the single `frontend/` application and select **Turnover prediction** in its sidebar. The screen calls the endpoints above; it does not use the earlier standalone Module 3 UI. If no model artifact is available, it shows a clear unavailable state rather than inventing a prediction.

## Production Decision Required

Before using real records, the team must agree the selected EESI formula/version, access control, feature definitions, the target observation window, approved de-identification method, and whether employee-level EESI is ethically permitted for the research purpose.
