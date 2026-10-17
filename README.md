# KND CDAP IT 01

## EESI progress presentation prototype

The independent EESI proof of concept is available under **EESI prototype** in the frontend sidebar. It compares three exploratory formulas using the existing pilot data and provides employee breakdowns, salary/economic scenarios, and downloadable calculation evidence. It works without Supabase or completed Module 1 uploads. These scores have not been empirically validated.

See [the PP1 demo and research evidence guide](docs/eesi/PP1-GUIDE.md) for setup, formulas, assessment mapping, tests, and remaining research. Reproduce pilot results with `python scripts/export_eesi_evidence.py`.

The EESI screen also includes aggregate results for **2,304 real LFS 2024 monthly salaried employees**, matched to official NCPI/inflation and quarterly unemployment. See [real-data preparation and limitations](docs/eesi/REAL-DATA.md). Reproduce with `python scripts/prepare_lfs2024.py` using an authorized local dataset copy. Raw and prepared microdata are excluded from Git.

Foundation for the **HR Attrition and Economic Data Analysis Platform**. The planned system will import HR and macroeconomic data, map economic indicators to employee events by month, validate the integrated data, and later train baseline attrition prediction models.

## Technology stack

| Area | Technology |
| --- | --- |
| Frontend | React + TypeScript + Vite |
| Backend | Python + FastAPI |
| Database | Supabase (hosted PostgreSQL) |
| Data / ML | Pandas, NumPy, scikit-learn |

## Project structure

```text
frontend/       React application
backend/        FastAPI application and tests
supabase/       SQL schema and Module 1 integration migration
pilot-data/     100-employee synthetic HR and six-month macroeconomic pilot data
```

## First-time setup

1. Install **Python 3.12+** and **Node.js 20+**.
2. Copy the environment template:

   ```powershell
   Copy-Item .env.example .env
   Copy-Item backend/.env.example backend/.env
   ```

3. Create a Supabase project at [Supabase](https://supabase.com/dashboard). In **Project Settings → API**, copy the Project URL and the `service_role` key into `backend/.env`. Never expose the service-role key in frontend code.
4. In the Supabase dashboard, open **SQL Editor**, create a **New query**, paste all of [schema.sql](supabase/schema.sql), and click **Run**. This creates the application tables and the private `dataset-files` bucket.
5. Install and run the backend:

   ```powershell
   cd backend
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8000
   ```

   API health check: http://localhost:8000/health. Interactive API documentation will be at http://localhost:8000/docs.
   After configuring Supabase, verify the connection at http://localhost:8000/api/v1/supabase/status.

6. In a second terminal, install and run the frontend:

   ```powershell
   cd frontend
   Copy-Item .env.example .env
   npm.cmd install
   npm.cmd run dev
   ```

   Open http://localhost:5173.

## Current starting points

- FastAPI health and status endpoints with CORS configured for the React app.
- Supabase client configuration for a hosted PostgreSQL database.
- Supabase schema plus register, login, and authenticated-user API endpoints.
- React/TypeScript/Vite application shell.
- Dependencies for CSV/Excel uploads, data processing, PDF export, and later ML experimentation.

## Authentication API

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | `/api/v1/auth/register` | Create a user |
| POST | `/api/v1/auth/login` | Get access and refresh tokens |
| GET | `/api/v1/auth/me` | Get the signed-in user; send `Authorization: Bearer <access_token>` |

After applying the SQL schema, the next feature is the HR dataset upload workflow.

## Module 1 database tables

Run [module1_data_integration_migration.sql](supabase/module1_data_integration_migration.sql) after the initial schema. It adds the Module 1 tables for data-cleaning runs and issues, temporal-mapping previews, validation issues, and downloadable dataset exports. It does not add EESI, ML, or retention-recommendation tables; those belong to the other team modules.

Run [module1_pilot_attributes_migration.sql](supabase/module1_pilot_attributes_migration.sql) after that migration to add the HR and macroeconomic attributes used by the 100-employee / six-month pilot dataset.
# Module 3 — Employee Turnover Prediction & Wellbeing Risk Analysis

This repository contains the Module 3 UI prototype and a separate, dataset-configurable Python baseline for employee turnover classification. Module 3 predicts a target class from approved HR features; it does not calculate EESI (Module 2) or generate retention recommendations (Module 4).

## Current Status

- **UI:** Module 3 is available in the unified `frontend/` application under **Turnover prediction**. It calls the FastAPI backend and displays saved-model results when a local artifact is available.
- **Prediction pipeline:** Implemented and unit-tested, but no approved research dataset is stored in this repository.
- **Evaluation:** Implemented for the held-out test split created by training. No research metrics are claimed until a real dataset run is completed.
- **EESI:** Optional input contract only; no Module 2 interface or EESI output was present.
- **Explainability:** The current SHAP visual in the UI is mock-only. No SHAP computation has been added because no trained research model or approved SHAP scope was present.

## Repository Structure

```text
frontend/         Unified React application for Modules 1, 2, and 3
backend/          Unified FastAPI application, including Module 3 prediction routes
module3_ml/       Python data validation, training, prediction, evaluation CLI
tests/            Synthetic unit tests only; not research data
docs/             PP1 evidence, demo script, research mapping, and integration contract
artifacts/        Local model/results output (ignored by Git)
```

## Setup

### Unified frontend

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

### ML pipeline

```powershell
py -m pip install -r requirements-ml.txt
```

The pipeline needs a legitimate, approved CSV dataset. Do not commit confidential employee data or model artifacts.

## Dataset Contract

The training command requires you to explicitly provide:

- `--data`: approved CSV path.
- `--target`: the actual existing turnover target column.
- `--features`: approved predictor columns, comma-separated.

Feature selection is deliberately explicit to prevent accidental use of identifiers or target-leakage fields. The loader reports missing values, duplicates, types, and target-class distribution. Numeric features receive median imputation and scaling; categorical features receive most-frequent imputation and one-hot encoding. These transformations are fitted only on the training split.

## Train

```powershell
py -m module3_ml.cli train --data path\to\approved_hr_data.csv --target <target_column> --features <feature_1>,<feature_2>,<feature_3>
```

This creates an ignored local artifact directory containing the trained pipeline, metadata, diagnostics, and a held-out test CSV. The baseline is Logistic Regression because it is transparent, produces class probabilities, and works well with mixed HR feature types after preprocessing.

## Predict

Create a local JSON file containing exactly the feature columns used during training. For example, if the features were `Age,OverTime`:

```json
{ "Age": 30, "OverTime": "Yes" }
```

Then run:

```powershell
py -m module3_ml.cli predict --record path\to\employee_record.json
```

The command returns the trained model's predicted class and probabilities. It rejects missing or unexpected fields and does not assign unsupported High/Medium/Low risk bands.

## Evaluate

```powershell
py -m module3_ml.cli evaluate
```

Evaluation uses only the held-out split saved during training and writes JSON and Markdown reports. It reports accuracy, macro precision, macro recall, macro F1, class-specific results, a labelled confusion matrix, and ROC-AUC when the binary held-out set permits it. Macro averaging weights each class equally; this is useful when class sizes differ.

## EESI Boundary

Module 2 owns EESI calculation. Once an interface exists, supply its precomputed column through `--eesi-column <column_name>` and include the same name in `--features`. Module 3 validates the field but does not invent or calculate EESI values.

## Tests

```powershell
py -m unittest discover -s tests -v
cd frontend
npm.cmd run build
```

The Python tests use a tiny synthetic fixture strictly for input, artifact, and evaluation-interface behaviour. They are not a research experiment and their results must not be reported as model performance.

## PP1 Documents

- `docs/PP1_EVIDENCE.md`
- `docs/PP1_DEMO_SCRIPT.md`
- `docs/PP1_RESEARCH_MAPPING.md`
- `docs/MODULE2_MODULE3_CONTRACT.md`
- `docs/PP1_PROJECT_EVIDENCE.md`
