# Module 3 Research Mapping

| Research objective | Implemented function | Evaluation method | Evidence |
| --- | --- | --- | --- |
| Build a reproducible turnover prediction baseline from HR data | `module3_ml.cli train` and `predict` | Validation diagnostics, saved pipeline, input-contract tests | Training log, artifact metadata, prediction log |
| Evaluate the classifier without training-set leakage | `module3_ml.cli evaluate` | Held-out stratified test set; accuracy, macro precision/recall/F1, ROC-AUC where valid, confusion matrix | Generated evaluation report |
| Prepare for HR + EESI comparison without implementing Module 2 | Optional `--eesi-column` contract | Use identical feature selection/split procedure once Module 2 supplies a real column | Module 2 schema agreement and future comparison report |

## EESI Integration Contract

Module 3 accepts EESI only as a precomputed, numeric feature column in the approved training CSV and in prediction records. The exact column name is passed through `--eesi-column` and must also appear in `--features`. Module 2 owns calculation, scale, timing, and data quality. Missing EESI fields are rejected at inference; no values are fabricated by Module 3.
