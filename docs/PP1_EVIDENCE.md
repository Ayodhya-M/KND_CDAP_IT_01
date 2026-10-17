# PP1 Evidence — Module 3

## Function 1: Employee Turnover Prediction Pipeline

- **Owner:** Module 3
- **Research objective:** Develop an explainable ML-based employee turnover prediction model using approved HR features, with an optional EESI input supplied by Module 2.
- **Input:** An approved CSV dataset, an explicit existing target column, explicitly selected feature columns, and a JSON employee record at inference.
- **Processing:** Validates data; performs a reproducible stratified train/test split; fits imputers, numeric scaling, categorical encoding, and a Logistic Regression baseline in one scikit-learn pipeline; saves trusted local artifacts.
- **Output:** Predicted target class and model class probabilities. The output is not a risk band or retention recommendation.
- **Dependencies:** Python, `pandas`, `scikit-learn`, an approved dataset, and an agreed Module 2 EESI column if EESI is used.
- **Demonstration:** Run `train`, then `predict` with a JSON record matching the saved feature contract.
- **Current status:** Partially complete. The code is implemented and unit-tested; no approved research dataset was present at implementation time, so no real training result or prediction is claimed.

## Function 2: Model Evaluation and Performance Analysis

- **Owner:** Module 3
- **Research objective:** Evaluate the baseline turnover classifier on a held-out split.
- **Input:** The held-out test set produced by the training command and its saved model artifact.
- **Processing:** Produces accuracy, macro precision/recall/F1, ROC-AUC when binary and computable, a class-specific report, and a labelled confusion matrix.
- **Output:** JSON and Markdown reports in the local, ignored artifact directory.
- **Dependencies:** A successful real training run.
- **Demonstration:** Run `evaluate --artifact-dir artifacts/module3` after training.
- **Current status:** Partially complete. Evaluation code and unit tests are implemented; actual research metrics await an approved dataset.

## Tests Performed and Actual Outcomes

- `py -m unittest discover -s tests -v`: **passed** — 6 tests. Covered valid prediction output, missing and unexpected feature rejection, saved-artifact loading, held-out evaluation shape/accuracy calculation, missing artifact handling, and missing dataset/EESI-field handling.
- `npm.cmd run build`: **passed** — Vite production build completed.
- Training with a deliberately missing CSV path: **failed as expected** with a readable dataset-not-found error. This confirms the pipeline does not generate a fake result when data is absent.
- Real approved-dataset training, prediction, and evaluation: **not run** — no approved dataset was available in the repository.

## Synthetic Pilot Integration Check

- `GET /api/v1/module3/pilot-export?formula_id=additive`: **implemented and tested**. It joins the existing Module 1 synthetic pilot features with one explicitly selected Module 2 EESI formula and version.
- End-to-end CLI flow: **completed locally** using the synthetic pilot export. Training created an 80/20 stratified split, prediction accepted the EESI feature, and evaluation reports were generated in ignored `artifacts/module3_synthetic/`.
- **Evidence boundary:** the pilot HR records and their Attrition labels are synthetic. Generated predictions and metrics demonstrate only that the integration and software pipeline run. They must not be presented as real-world performance, EESI validation, or evidence that EESI improves turnover prediction.

## Evidence Still Required

- Screenshot or terminal log of training with the approved dataset.
- Screenshot or terminal log of a real prediction record and output.
- Generated `evaluation_report.md` from the approved dataset.
- Screenshot of unit-test output and Git history.
- Research diary entry describing feature selection, dataset source/permission, target definition, and limitations.
