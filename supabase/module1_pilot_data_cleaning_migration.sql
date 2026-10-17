-- Module 1 pilot data-cleaning support without login/session.
-- Run once after module1_data_integration_migration.sql.

ALTER TABLE public.data_cleaning_runs
    ALTER COLUMN initiated_by DROP NOT NULL;
