# Turnover prediction progress demo

From the project root, using the backend virtual environment:

```powershell
.\backend\.venv\Scripts\python.exe scripts/prepare_module3_demo.py
```

This creates local ignored artifacts in `artifacts/module3_synthetic`, the default
backend model location. It exports the 300-row synthetic HR pilot, computes the
exploratory additive EESI using each employee's 2023 observation month, trains
the existing Logistic Regression pipeline, and evaluates its saved 60-row
held-out split (240 training rows). Preprocessing is fitted on training only.
`--formula economic` and `--formula interaction` support separate comparisons;
use `--output` with a different directory to preserve an existing model. The
setup refuses to overwrite an existing saved pipeline.

The model metadata records the source checksum, feature contract, class labels,
split and EESI formula/version. Model files are local: another checkout or
computer must run setup independently. Do not commit binary artifacts.

Start the backend and frontend, open **Turnover Analytics**, and refresh model
status. Select a synthetic employee to load all eight features and a calculated
EESI matching the model. Prediction returns a class and class probabilities.
**Show held-out evaluation** loads saved test metrics and the confusion matrix.
Editing inputs clears the previous prediction. Custom input mode requires a
separately supplied EESI consistent with the model's displayed formula; it does
not recalculate EESI after manual changes to salary or other fields.

The selector rejects model/feature/EESI-version mismatches rather than silently
using a different reference profile. The backend rejects nonfinite, out-of-range,
blank and invalid categorical inputs. No HIES respondents or household finances
are joined to these synthetic employees: HIES has no attrition labels.

All employee data and attrition labels in this demo are synthetic. Held-out
metrics demonstrate software behavior only, not research performance or
validated employee risk. No high/medium/low risk thresholds or SHAP explanations
are claimed. Module 4's real explanation and risk-classification contracts
remain separate work.
