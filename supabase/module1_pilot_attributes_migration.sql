-- KND CDAP IT 01 - Module 1 pilot-data attributes
-- Run once after schema.sql and module1_data_integration_migration.sql.

ALTER TABLE public.employee_records
    ADD COLUMN IF NOT EXISTS gender TEXT CHECK (gender IN ('Female', 'Male', 'Other')),
    ADD COLUMN IF NOT EXISTS job_role TEXT,
    ADD COLUMN IF NOT EXISTS job_level SMALLINT CHECK (job_level BETWEEN 1 AND 5),
    ADD COLUMN IF NOT EXISTS business_travel TEXT CHECK (business_travel IN ('Non-Travel', 'Travel_Rarely', 'Travel_Frequently')),
    ADD COLUMN IF NOT EXISTS distance_from_home SMALLINT CHECK (distance_from_home >= 0),
    ADD COLUMN IF NOT EXISTS education_field TEXT,
    ADD COLUMN IF NOT EXISTS marital_status TEXT,
    ADD COLUMN IF NOT EXISTS overtime BOOLEAN,
    ADD COLUMN IF NOT EXISTS job_satisfaction SMALLINT CHECK (job_satisfaction BETWEEN 1 AND 4),
    ADD COLUMN IF NOT EXISTS environment_satisfaction SMALLINT CHECK (environment_satisfaction BETWEEN 1 AND 4),
    ADD COLUMN IF NOT EXISTS work_life_balance SMALLINT CHECK (work_life_balance BETWEEN 1 AND 4),
    ADD COLUMN IF NOT EXISTS total_working_years SMALLINT CHECK (total_working_years >= 0),
    ADD COLUMN IF NOT EXISTS years_at_company SMALLINT CHECK (years_at_company >= 0);

ALTER TABLE public.economic_indicators
    ADD COLUMN IF NOT EXISTS cpi_index NUMERIC(12, 4),
    ADD COLUMN IF NOT EXISTS policy_interest_rate_percent NUMERIC(7, 4),
    ADD COLUMN IF NOT EXISTS usd_lkr_exchange_rate NUMERIC(12, 4),
    ADD COLUMN IF NOT EXISTS gdp_growth_rate_percent NUMERIC(7, 4);

ALTER TABLE public.integrated_records
    ADD COLUMN IF NOT EXISTS gender TEXT,
    ADD COLUMN IF NOT EXISTS job_role TEXT,
    ADD COLUMN IF NOT EXISTS job_level SMALLINT,
    ADD COLUMN IF NOT EXISTS overtime BOOLEAN,
    ADD COLUMN IF NOT EXISTS job_satisfaction SMALLINT,
    ADD COLUMN IF NOT EXISTS work_life_balance SMALLINT,
    ADD COLUMN IF NOT EXISTS cpi_index NUMERIC(12, 4),
    ADD COLUMN IF NOT EXISTS policy_interest_rate_percent NUMERIC(7, 4),
    ADD COLUMN IF NOT EXISTS usd_lkr_exchange_rate NUMERIC(12, 4),
    ADD COLUMN IF NOT EXISTS gdp_growth_rate_percent NUMERIC(7, 4);

COMMENT ON COLUMN public.employee_records.salary IS 'Monthly income/salary from the HR pilot dataset.';
COMMENT ON COLUMN public.economic_indicators.indicator_month IS 'First day of the monthly reporting period.';
