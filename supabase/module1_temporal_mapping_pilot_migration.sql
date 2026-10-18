-- Module 1 pilot temporal-mapping support without login/session.
-- Run once after module1_data_integration_migration.sql.

ALTER TABLE public.temporal_mapping_runs
    ALTER COLUMN initiated_by DROP NOT NULL,
    ALTER COLUMN employee_date_field SET DEFAULT 'observation_date';

ALTER TABLE public.temporal_mapping_runs
    DROP CONSTRAINT IF EXISTS temporal_mapping_runs_employee_date_field_check;

ALTER TABLE public.temporal_mapping_runs
    ADD CONSTRAINT temporal_mapping_runs_employee_date_field_check
    CHECK (employee_date_field IN ('observation_date', 'join_date', 'resignation_date'));
