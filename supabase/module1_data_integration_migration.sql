-- KND CDAP IT 01 - Module 1: HR & Macroeconomic Data Integration
-- Run this file once in Supabase Dashboard > SQL Editor.
-- It extends the existing schema with tables owned by Module 1 only.

CREATE TABLE IF NOT EXISTS public.data_cleaning_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    upload_id UUID NOT NULL REFERENCES public.dataset_uploads(id) ON DELETE CASCADE,
    initiated_by UUID NOT NULL REFERENCES public.profiles(id),
    action_type TEXT NOT NULL CHECK (action_type IN (
        'analyse', 'remove_missing', 'remove_duplicates', 'standardise_dates'
    )),
    rows_before INTEGER NOT NULL DEFAULT 0,
    rows_after INTEGER NOT NULL DEFAULT 0,
    affected_row_count INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS public.data_quality_issues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    upload_id UUID NOT NULL REFERENCES public.dataset_uploads(id) ON DELETE CASCADE,
    cleaning_run_id UUID REFERENCES public.data_cleaning_runs(id) ON DELETE SET NULL,
    row_number INTEGER,
    column_name TEXT,
    issue_type TEXT NOT NULL CHECK (issue_type IN ('missing_value', 'duplicate_record', 'invalid_date', 'invalid_value')),
    issue_value TEXT,
    is_resolved BOOLEAN NOT NULL DEFAULT FALSE,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS public.temporal_mapping_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hr_upload_id UUID NOT NULL REFERENCES public.dataset_uploads(id),
    economic_upload_id UUID NOT NULL REFERENCES public.dataset_uploads(id),
    initiated_by UUID NOT NULL REFERENCES public.profiles(id),
    employee_date_field TEXT NOT NULL DEFAULT 'resignation_date'
        CHECK (employee_date_field IN ('join_date', 'resignation_date')),
    total_employee_records INTEGER NOT NULL DEFAULT 0,
    mapped_record_count INTEGER NOT NULL DEFAULT 0,
    unmapped_record_count INTEGER NOT NULL DEFAULT 0,
    mapping_accuracy NUMERIC(5, 2) CHECK (mapping_accuracy BETWEEN 0 AND 100),
    status TEXT NOT NULL DEFAULT 'preview'
        CHECK (status IN ('preview', 'confirmed', 'processing', 'completed', 'failed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    confirmed_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    CHECK (hr_upload_id <> economic_upload_id)
);

CREATE TABLE IF NOT EXISTS public.temporal_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mapping_run_id UUID NOT NULL REFERENCES public.temporal_mapping_runs(id) ON DELETE CASCADE,
    employee_record_id UUID NOT NULL REFERENCES public.employee_records(id) ON DELETE CASCADE,
    economic_indicator_id UUID REFERENCES public.economic_indicators(id) ON DELETE SET NULL,
    employee_event_date DATE,
    mapped_month DATE,
    mapping_status TEXT NOT NULL DEFAULT 'mapped' CHECK (mapping_status IN ('mapped', 'unmapped', 'invalid_date')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (mapping_run_id, employee_record_id)
);

ALTER TABLE public.integration_runs
    ADD COLUMN IF NOT EXISTS temporal_mapping_run_id UUID
    REFERENCES public.temporal_mapping_runs(id);

ALTER TABLE public.integrated_records
    ADD COLUMN IF NOT EXISTS temporal_mapping_id UUID
    REFERENCES public.temporal_mappings(id) ON DELETE SET NULL;

CREATE TABLE IF NOT EXISTS public.validation_issues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    validation_report_id UUID NOT NULL REFERENCES public.validation_reports(id) ON DELETE CASCADE,
    record_reference TEXT,
    column_name TEXT,
    issue_type TEXT NOT NULL CHECK (issue_type IN ('missing_value', 'duplicate_record', 'invalid_date', 'unmapped_economic_data')),
    issue_value TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.dataset_exports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    requested_by UUID NOT NULL REFERENCES public.profiles(id),
    upload_id UUID REFERENCES public.dataset_uploads(id) ON DELETE SET NULL,
    integration_run_id UUID REFERENCES public.integration_runs(id) ON DELETE SET NULL,
    export_type TEXT NOT NULL CHECK (export_type IN ('cleaned_hr', 'cleaned_economic', 'integrated_dataset', 'validation_report')),
    file_format TEXT NOT NULL CHECK (file_format IN ('csv', 'xlsx', 'pdf')),
    storage_path TEXT,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'generating', 'completed', 'failed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS data_cleaning_runs_upload_id_idx ON public.data_cleaning_runs(upload_id);
CREATE INDEX IF NOT EXISTS data_quality_issues_upload_id_idx ON public.data_quality_issues(upload_id);
CREATE INDEX IF NOT EXISTS temporal_mappings_run_id_idx ON public.temporal_mappings(mapping_run_id);
CREATE INDEX IF NOT EXISTS temporal_mappings_employee_record_id_idx ON public.temporal_mappings(employee_record_id);
CREATE INDEX IF NOT EXISTS validation_issues_report_id_idx ON public.validation_issues(validation_report_id);
CREATE INDEX IF NOT EXISTS dataset_exports_requested_by_idx ON public.dataset_exports(requested_by);

ALTER TABLE public.data_cleaning_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.data_quality_issues ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.temporal_mapping_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.temporal_mappings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.validation_issues ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dataset_exports ENABLE ROW LEVEL SECURITY;

COMMENT ON TABLE public.data_cleaning_runs IS 'Module 1 cleaning actions applied to an uploaded HR or economic dataset.';
COMMENT ON TABLE public.temporal_mapping_runs IS 'Module 1 preview and confirmation of employee-event dates mapped to monthly economic indicators.';
COMMENT ON TABLE public.integrated_records IS 'Module 1 final integrated output: HR features, mapped macroeconomic indicators, and attrition label.';
