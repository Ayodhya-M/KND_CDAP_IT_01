-- Module 1 → Module 2 handover fields for the pilot project.
-- Run once after module1_pilot_integration_migration.sql.

ALTER TABLE public.employee_records
    ADD COLUMN IF NOT EXISTS additional_income NUMERIC(14, 2)
    CHECK (additional_income >= 0);

ALTER TABLE public.integrated_records
    ADD COLUMN IF NOT EXISTS tenure_years SMALLINT
    CHECK (tenure_years >= 0),
    ADD COLUMN IF NOT EXISTS additional_income NUMERIC(14, 2)
    CHECK (additional_income >= 0);

COMMENT ON COLUMN public.employee_records.additional_income IS
    'Synthetic monthly overtime/additional income used in the Module 1 pilot.';
COMMENT ON COLUMN public.integrated_records.tenure_years IS
    'Tenure at the company in years, sourced from employee_records.years_at_company.';
COMMENT ON COLUMN public.integrated_records.additional_income IS
    'Monthly overtime/additional income included in the Module 1 → Module 2 handover dataset.';
