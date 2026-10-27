# PP1 Project Evidence Matrix

This matrix separates verified implementation evidence from work that remains. It does not claim final research validity or a completion percentage.

| Module | Implemented | Demonstrable | Pending before final research claims |
| --- | --- | --- | --- |
| **1 — Hybrid Data Integration** | HR/macro CSV validation, Supabase persistence routes, missing-value cleaning, temporal month mapping, synthetic pilot data | Backend tests: 48 passed locally; frontend screens tested locally | Approved real-data workflow, production access controls, ML-ready real-data export approval |
| **2 — EESI** | Versioned candidate formulas, scenario API, pilot/aggregate views, real-data aggregate preparation, limitations documentation | Backend tests included in 48 passed locally; EESI frontend tested locally | Independent stress validation, sensitivity analysis, final formula selection |
| **3 — Turnover Prediction** | Configurable Logistic Regression pipeline, preprocessing, saved artifacts, input validation, held-out evaluation, synthetic pilot export contract | Module 3 unit tests: 6 passed; root UI build passed; pilot export endpoint tests: 4 passed; synthetic end-to-end CLI flow completed | Approved turnover dataset, real training/evaluation, verified SHAP scope, approved EESI candidate comparison |
| **4 — Recommendations** | No implementation identified in this repository audit | None | Recommendation rules/engine, validation, integration with outputs from Modules 2 and 3 |

## PP1 Demonstration Order

1. Module 1: upload/validate synthetic pilot HR and macroeconomic CSVs, then show month mapping.
2. Module 2: show one EESI scenario and the selected formula/version metadata.
3. Module 3: show the contract endpoint, download the pilot-only export, train/predict/evaluate, and state that all resulting metrics are synthetic technical evidence.
4. Show automated-test outputs and explain the remaining approved-data and ethics dependencies.
