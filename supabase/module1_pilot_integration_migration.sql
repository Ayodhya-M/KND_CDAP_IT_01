-- Module 1 pilot integration support without login/session.
-- Run once after schema.sql and the Module 1 migrations.

ALTER TABLE public.integration_runs
    ALTER COLUMN initiated_by DROP NOT NULL;

ALTER TABLE public.integrated_records
    ADD COLUMN IF NOT EXISTS employee_id TEXT,
    ADD COLUMN IF NOT EXISTS observation_date DATE;

CREATE INDEX IF NOT EXISTS integrated_records_observation_date_idx
    ON public.integrated_records(observation_date);

COMMENT ON COLUMN public.integrated_records.employee_id IS
    'Employee identifier copied into the unified Module 1 output for preview and export.';
COMMENT ON COLUMN public.integrated_records.observation_date IS
    'Employee temporal context used to map this unified record to the economic month.';
