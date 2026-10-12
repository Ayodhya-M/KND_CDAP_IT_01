const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'

export type HrUploadError = {
  field: string
  message: string
  count?: number
  sample_rows?: number[]
  columns?: string[]
}

export type HrUploadSummary = {
  status: 'success' | 'validation_failed'
  file_name: string
  total_records?: number
  valid_records?: number
  invalid_records?: number
  duplicate_employee_ids?: number
  missing_values?: Record<string, number>
  observation_period?: { start: string; end: string } | null
  errors?: HrUploadError[]
  upload_id?: string
}

export type MacroUploadSummary = {
  status: 'success' | 'validation_failed'
  file_name: string
  total_records?: number
  valid_records?: number
  invalid_records?: number
  duplicate_months?: number
  missing_values?: Record<string, number>
  economic_period?: { start: string; end: string } | null
  errors?: HrUploadError[]
  upload_id?: string
}

export type MappingUploadChoice = {
  id: string
  original_filename: string
  record_count: number
  uploaded_at: string
}

export type TemporalMappingRow = {
  employee_id: string
  observation_date: string | null
  economic_month: string | null
  status: 'mapped' | 'unmapped' | 'invalid_date'
}

export type TemporalMappingPreview = {
  status: 'success'
  mapping_run_id: string
  total_employee_records: number
  matched_records: number
  unmatched_records: number
  mapping_rate: number
  mappings: TemporalMappingRow[]
}

export type CleaningUploadChoice = {
  id: string
  dataset_type: 'hr' | 'economic'
  original_filename: string
  record_count: number
  uploaded_at: string
}

export type CleaningAnalysis = {
  status: 'success'
  cleaning_run_id: string
  total_records: number
  rows_with_missing_values: number
  missing_values: Record<string, number>
  sample_row_numbers: number[]
}

export type RemoveMissingResult = {
  status: 'success'
  cleaning_run_id: string
  source_upload_id: string
  cleaned_upload_id: string
  rows_before: number
  rows_after: number
  removed_records: number
  missing_values: Record<string, number>
  message: string
}

type ApiErrorBody = HrUploadSummary & { detail?: string }

export class UploadRequestError extends Error {
  constructor(readonly body: ApiErrorBody) {
    super(body.detail ?? body.errors?.[0]?.message ?? 'HR upload validation failed')
  }

  get validationSummary(): HrUploadSummary | null {
    return this.body.status === 'validation_failed' ? this.body : null
  }
}

export async function uploadHrDataset(file: File): Promise<HrUploadSummary> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${API_BASE_URL}/hr/upload`, { method: 'POST', body: formData })
  const body = await response.json().catch(() => ({})) as ApiErrorBody
  if (!response.ok) throw new UploadRequestError(body)
  return body
}

export async function uploadMacroeconomicDataset(file: File): Promise<MacroUploadSummary> {
  const formData = new FormData()
  formData.append('file', file)
  const response = await fetch(`${API_BASE_URL}/macroeconomic/upload`, { method: 'POST', body: formData })
  const body = await response.json().catch(() => ({})) as ApiErrorBody
  if (!response.ok) throw new UploadRequestError(body)
  return body as MacroUploadSummary
}

export async function getMappingUploadChoices(): Promise<{
  hr_uploads: MappingUploadChoice[]
  economic_uploads: MappingUploadChoice[]
}> {
  const response = await fetch(`${API_BASE_URL}/temporal-mapping/uploads`)
  const body = await response.json().catch(() => ({})) as ApiErrorBody
  if (!response.ok) throw new UploadRequestError(body)
  return body as unknown as { hr_uploads: MappingUploadChoice[]; economic_uploads: MappingUploadChoice[] }
}

export async function createTemporalMappingPreview(hrUploadId: string, economicUploadId: string): Promise<TemporalMappingPreview> {
  const response = await fetch(`${API_BASE_URL}/temporal-mapping/preview`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ hr_upload_id: hrUploadId, economic_upload_id: economicUploadId }),
  })
  const body = await response.json().catch(() => ({})) as ApiErrorBody
  if (!response.ok) throw new UploadRequestError(body)
  return body as unknown as TemporalMappingPreview
}

export async function getCleaningUploadChoices(): Promise<{ uploads: CleaningUploadChoice[] }> {
  const response = await fetch(`${API_BASE_URL}/data-cleaning/uploads`)
  const body = await response.json().catch(() => ({})) as ApiErrorBody
  if (!response.ok) throw new UploadRequestError(body)
  return body as unknown as { uploads: CleaningUploadChoice[] }
}

export async function analyseMissingValues(uploadId: string): Promise<CleaningAnalysis> {
  const response = await fetch(`${API_BASE_URL}/data-cleaning/analyse/${uploadId}`)
  const body = await response.json().catch(() => ({})) as ApiErrorBody
  if (!response.ok) throw new UploadRequestError(body)
  return body as unknown as CleaningAnalysis
}

export async function removeMissingValues(uploadId: string): Promise<RemoveMissingResult> {
  const response = await fetch(`${API_BASE_URL}/data-cleaning/remove-missing`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ upload_id: uploadId }),
  })
  const body = await response.json().catch(() => ({})) as ApiErrorBody
  if (!response.ok) throw new UploadRequestError(body)
  return body as unknown as RemoveMissingResult
}
