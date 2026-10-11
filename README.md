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
