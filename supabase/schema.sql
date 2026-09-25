-- KND CDAP IT 01: Supabase schema
-- Run this entire file in Supabase Dashboard > SQL Editor > New query.

CREATE TABLE public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name TEXT,
    role TEXT NOT NULL DEFAULT 'researcher' CHECK (role IN ('researcher', 'admin')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE OR REPLACE FUNCTION public.create_profile_for_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER SET search_path = public
AS $$
BEGIN
    INSERT INTO public.profiles (id, full_name)
    VALUES (NEW.id, NEW.raw_user_meta_data ->> 'full_name');
    RETURN NEW;
END;
$$;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE PROCEDURE public.create_profile_for_new_user();

CREATE TABLE public.dataset_uploads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    uploaded_by UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    dataset_type TEXT NOT NULL CHECK (dataset_type IN ('hr', 'economic')),
    original_filename TEXT NOT NULL,
    file_format TEXT NOT NULL CHECK (file_format IN ('csv', 'xlsx', 'xls')),
    storage_path TEXT,
    record_count INTEGER NOT NULL DEFAULT 0 CHECK (record_count >= 0),
    processing_status TEXT NOT NULL DEFAULT 'uploaded'
        CHECK (processing_status IN ('uploaded', 'cleaned', 'integrated', 'failed')),
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE public.employee_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    upload_id UUID NOT NULL REFERENCES public.dataset_uploads(id) ON DELETE CASCADE,
    employee_id TEXT NOT NULL,
    age SMALLINT CHECK (age BETWEEN 14 AND 100),
    salary NUMERIC(14, 2) CHECK (salary >= 0),
    department TEXT,
    join_date DATE,
    resignation_date DATE,
    attrition BOOLEAN NOT NULL DEFAULT FALSE,
    raw_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (upload_id, employee_id),
    CHECK (resignation_date IS NULL OR join_date IS NULL OR resignation_date >= join_date)
);

CREATE TABLE public.economic_indicators (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    upload_id UUID NOT NULL REFERENCES public.dataset_uploads(id) ON DELETE CASCADE,
    indicator_month DATE NOT NULL,
    inflation_rate NUMERIC(7, 4),
    unemployment_rate NUMERIC(7, 4),
    cost_of_living_index NUMERIC(12, 4),
    raw_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (upload_id, indicator_month),
    CHECK (EXTRACT(DAY FROM indicator_month) = 1)
);

CREATE TABLE public.validation_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    upload_id UUID NOT NULL UNIQUE REFERENCES public.dataset_uploads(id) ON DELETE CASCADE,
    total_records INTEGER NOT NULL DEFAULT 0,
    missing_value_count INTEGER NOT NULL DEFAULT 0,
    duplicate_record_count INTEGER NOT NULL DEFAULT 0,
    invalid_date_count INTEGER NOT NULL DEFAULT 0,
    validation_status TEXT NOT NULL DEFAULT 'pending'
        CHECK (validation_status IN ('pending', 'passed', 'failed')),
    report_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE public.integration_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hr_upload_id UUID NOT NULL REFERENCES public.dataset_uploads(id),
    economic_upload_id UUID NOT NULL REFERENCES public.dataset_uploads(id),
    initiated_by UUID NOT NULL REFERENCES public.profiles(id),
    total_hr_records INTEGER NOT NULL DEFAULT 0,
    mapped_record_count INTEGER NOT NULL DEFAULT 0,
    mapping_accuracy NUMERIC(5, 2) CHECK (mapping_accuracy BETWEEN 0 AND 100),
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'processing', 'successful', 'failed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    CHECK (hr_upload_id <> economic_upload_id)
);

CREATE TABLE public.integrated_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    integration_run_id UUID NOT NULL REFERENCES public.integration_runs(id) ON DELETE CASCADE,
    employee_record_id UUID NOT NULL REFERENCES public.employee_records(id) ON DELETE CASCADE,
    economic_indicator_id UUID REFERENCES public.economic_indicators(id) ON DELETE SET NULL,
    mapped_month DATE,
    age SMALLINT,
    salary NUMERIC(14, 2),
    department TEXT,
    inflation_rate NUMERIC(7, 4),
    unemployment_rate NUMERIC(7, 4),
    cost_of_living_index NUMERIC(12, 4),
    attrition BOOLEAN NOT NULL,
    UNIQUE (integration_run_id, employee_record_id)
);

CREATE INDEX employee_records_upload_id_idx ON public.employee_records(upload_id);
CREATE INDEX employee_records_resignation_date_idx ON public.employee_records(resignation_date);
CREATE INDEX economic_indicators_month_idx ON public.economic_indicators(indicator_month);
CREATE INDEX integrated_records_run_idx ON public.integrated_records(integration_run_id);

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dataset_uploads ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.employee_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.economic_indicators ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.validation_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.integration_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.integrated_records ENABLE ROW LEVEL SECURITY;

-- FastAPI uses the service-role key and bypasses RLS. No browser-side database
-- access is permitted until feature-specific RLS policies are added.
INSERT INTO storage.buckets (id, name, public)
VALUES ('dataset-files', 'dataset-files', FALSE)
ON CONFLICT (id) DO NOTHING;
