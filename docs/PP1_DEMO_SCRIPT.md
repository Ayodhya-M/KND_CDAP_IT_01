# PP1 Live Demo Script — Module 3

> Do not use the synthetic test fixture as research evidence. Use only an approved, non-confidential dataset.

## Technical Integration Demonstration (Synthetic Pilot Only)

Use this short flow to prove Module 1 → Module 2 → Module 3 data compatibility. State that every output is technical demonstration evidence only.

1. Start the unified backend and frontend:

   ```powershell
   cd backend
   .\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
   ```

   ```powershell
   cd frontend
   npm.cmd run dev
   ```

2. Open the single frontend URL, select **Turnover prediction**, and show the loaded model status and EESI formula/version.
3. Show `GET /api/v1/module3/integration-contract` and explain that `EESIFormulaId` and `EESIFormulaVersion` provide reproducibility.
4. Download one selected formula's export:

   ```powershell
   Invoke-WebRequest http://localhost:8000/api/v1/module3/pilot-export?formula_id=additive -OutFile artifacts\module3_synthetic_pilot.csv
   ```

5. Train and evaluate using the commands in `docs/MODULE2_MODULE3_CONTRACT.md`, then refresh the integrated frontend and use its prediction/evaluation actions.
6. State clearly: “This proves the integration pipeline. The HR data and Attrition labels are synthetic, so these results are not research findings.”

## Approved Dataset Demonstration

1. Install ML dependencies: `py -m pip install -r requirements-ml.txt`.
2. Identify the actual CSV target and approved predictor columns. Do not include identifiers or post-outcome fields.
3. Train the baseline:

   ```powershell
   py -m module3_ml.cli train --data path\to\approved_hr_data.csv --target <actual_target_column> --features <feature_1>,<feature_2>,<feature_3>
   ```

4. Show `artifacts/module3/training_diagnostics.json` and explain that preprocessing was fit on training data only.
5. Create a local JSON record containing exactly the feature columns, then run:

   ```powershell
   py -m module3_ml.cli predict --record path\to\employee_record.json
   ```

6. Explain the actual predicted class and its probabilities. Do not describe it as a retention recommendation.
7. Run the held-out evaluation:

   ```powershell
   py -m module3_ml.cli evaluate
   ```

8. Show `artifacts/module3/evaluation_report.md`, including the confusion matrix and limitations.
9. Show a failure scenario by omitting a required field from the JSON record; the CLI should report the missing field.
10. Run the automated tests:

   ```powershell
   py -m unittest discover -s tests -v
   ```

11. State the current limitation: EESI is only accepted when Module 2 supplies an agreed, valid column; Module 3 does not calculate EESI.
