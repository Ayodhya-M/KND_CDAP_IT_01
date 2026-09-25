-- KND CDAP IT 01 - Module 1 temporal-context support
-- Run once after the existing schema and Module 1 migrations.
-- New HR records must have an observation date in the Jan-Jun 2023 pilot period.

ALTER TABLE public.employee_records
    ADD COLUMN IF NOT EXISTS observation_date DATE;

-- NOT VALID keeps existing legacy rows untouched while enforcing the requirement
-- for all new or updated HR records. Validate it after any legacy rows have been
-- populated with a real observation date.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'employee_records_observation_date_pilot_period_check'
          AND conrelid = 'public.employee_records'::regclass
    ) THEN
        ALTER TABLE public.employee_records
            ADD CONSTRAINT employee_records_observation_date_pilot_period_check
            CHECK (
                observation_date IS NOT NULL
                AND observation_date BETWEEN DATE '2023-01-01' AND DATE '2023-06-30'
            ) NOT VALID;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS employee_records_observation_date_idx
    ON public.employee_records(observation_date);

COMMENT ON COLUMN public.employee_records.observation_date IS
    'Required temporal context for an HR record. Module 1 pilot values must be between 2023-01-01 and 2023-06-30.';
