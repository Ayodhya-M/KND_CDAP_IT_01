const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'

export type HiesCalculation = {
  scores: Record<string, number>; components: Record<string, number>
  contributions: Record<string, Record<string, number>>; warnings: string[]; version: string
}
export type HiesScenario = { salary: number; inflation: number; cpi: number; unemployment: number; reference_salary: number }
export type HiesRecord = {
  sample_id: string; survey_month: string; economic_month: string
  salary: number; extra_pay: number | null; bonus_monthly: number | null
  household_expenditure: number; household_debt_payments: number | null
  scores: Record<string, number>
  total_income: number | null; household_food: number; household_nonfood: number
  outstanding_debt_known: number | null; quality_flags: string[]
  inflation: number; cpi: number; unemployment: number; breakdown: HiesCalculation
}
export type HiesDataset = {
  record_count: number; prepared_available: boolean; imported_at: string | null
  records: HiesRecord[]; complete_income_count: number; debt_payment_count: number; note: string
  metadata: { formulas: { id: string; name: string; expression: string; rationale: string }[]; bounds: Record<string, number[]>; reference_salary: number; reference_period: string; cpi_base: string }
}
export async function calculateHiesScenario(payload: HiesScenario): Promise<HiesCalculation> {
  const response = await fetch(`${API_BASE_URL}/eesi/hies/scenario`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
  const body = await response.json()
  if (!response.ok) throw new Error(typeof body.detail === 'string' ? body.detail : 'Enter valid scenario values.')
  return body as HiesCalculation
}
export async function getHiesDataset(importPrepared = false): Promise<HiesDataset> {
  const response = await fetch(`${API_BASE_URL}/eesi/hies${importPrepared ? '/import-prepared' : ''}`, { method: importPrepared ? 'POST' : 'GET' })
  const body = await response.json()
  if (!response.ok) throw new Error(typeof body.detail === 'string' ? body.detail : 'Unable to load HIES data.')
  return body as HiesDataset
}

export async function getDatabaseStatus(): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/supabase/status`)
  const body = await response.json()
  if (!response.ok) throw new Error(typeof body.detail === 'string' ? body.detail : 'HR database unavailable.')
  return body.status as string
}

export type HrUploadError = {
  field: string
  message: string
  count?: number
  sample_rows?: number[]
  columns?: string[]
}

export type HrUploadSummary = {
  duplicate_upload?: boolean
  message?: string
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
  duplicate_upload?: boolean
  message?: string
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

export type Module4RiskFactor = {
  feature_name: string
  feature_value: unknown
  contribution: number
}

export type Module4Recommendation = {
  recommendation_id: string
  recommendation_type: string
  title: string
  category: string
  related_factor: string
  explanation: string
  suggested_action: string
  priority_score: number
  priority_level: string
}

export type Module4Metadata = {
  data_mode: string
  module2_source: string
  module3_source: string
  disclaimer: string
}

export type Module4RecommendationResponse = {
  employee_id: string
  employee_profile: {
    department: string | null
    job_role: string | null
    job_level: number | null
    salary: number | null
    overtime: boolean | null
    job_satisfaction: number | null
    work_life_balance: number | null
    years_at_company: number | null
  }
  turnover_probability: number
  risk_level: string
  eesi_score: number
  economic_pressure_level: string
  important_risk_factors: Module4RiskFactor[]
  recommendations: Module4Recommendation[]
  metadata: Module4Metadata
}

export type WhatIfChanges = {
  salary?: number
  overtime?: boolean
  job_satisfaction?: number
  work_life_balance?: number
}

export type ScenarioValues = {
  salary: number | null
  overtime: boolean | null
  job_satisfaction: number | null
  work_life_balance: number | null
}

export type WhatIfSimulationResponse = {
  employee_id: string
  label: string
  original_values: ScenarioValues
  simulated_values: ScenarioValues
  original_turnover_probability: number
  simulated_turnover_probability: number
  probability_difference: number
  original_recommendations: Module4Recommendation[]
  simulated_recommendations: Module4Recommendation[]
  removed_risk_factors: string[]
  retained_risk_factors: string[]
  assumptions: string[]
  disclaimer: string
  metadata: Module4Metadata
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

export type IntegrationMappingRun = {
  id: string
  total_employee_records: number
  mapped_record_count: number
  unmapped_record_count: number
  mapping_accuracy: number
  created_at: string
}

export type IntegratedRecordPreview = {
  employee_id: string
  salary: number
  tenure_years: number
  additional_income: number
  overtime: boolean
  job_satisfaction: number
  observation_date: string
  economic_month: string
  inflation_rate: number
  cpi_index: number
  unemployment_rate: number
  policy_interest_rate_percent: number
  usd_lkr_exchange_rate: number
  gdp_growth_rate_percent: number
  attrition: boolean
}

export type IntegrationResult = {
  status: 'success'
  integration_run_id: string
  total_hr_records: number
  integrated_records: number
  unmatched_records: number
  integration_rate: number
  records: IntegratedRecordPreview[]
}

export type ValidationIntegrationRun = {
  id: string
  total_hr_records: number
  mapped_record_count: number
  mapping_accuracy: number
  status: string
  created_at: string
}

export type DatasetValidationReport = {
  status: 'success'
  integration_run_id: string
  total_hr_records: number
  economic_months: number
  integrated_records: number
  missing_values: Record<string, number>
  missing_value_count: number
  duplicate_records: number
  invalid_values: { field: string; count: number; sample_employee_ids: string[] }[]
  invalid_value_count: number
  unmatched_records: number
  mapping_rate: number
  integration_rate: number
  record_count_consistency: {
    hr_records_equal_mapping_records: boolean
    integrated_records_equal_mapped_records: boolean
    expected_integrated_records: number
    actual_integrated_records: number
    is_consistent: boolean
  }
  validation_status: 'passed' | 'failed'
}

type ApiErrorBody = HrUploadSummary & { detail?: string }

export class UploadRequestError extends Error {
  constructor(readonly body: ApiErrorBody, readonly status = 0) {
    super(body.detail ?? body.errors?.[0]?.message ?? 'HR upload validation failed')
  }

  get validationSummary(): HrUploadSummary | null {
    return this.body.status === 'validation_failed' ? this.body : null
  }
}

export class RetentionRequestError extends Error {
  constructor(readonly status: number, message: string) {
    super(message)
    this.name = 'RetentionRequestError'
  }
}

export async function uploadHrDataset(file: File): Promise<HrUploadSummary> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${API_BASE_URL}/hr/upload`, { method: 'POST', body: formData })
  const body = await response.json().catch(() => ({})) as ApiErrorBody
  if (!response.ok) throw new UploadRequestError(body, response.status)
  return body
}

export async function uploadMacroeconomicDataset(file: File): Promise<MacroUploadSummary> {
  const formData = new FormData()
  formData.append('file', file)
  const response = await fetch(`${API_BASE_URL}/macroeconomic/upload`, { method: 'POST', body: formData })
  const body = await response.json().catch(() => ({})) as ApiErrorBody
  if (!response.ok) throw new UploadRequestError(body, response.status)
  return body as MacroUploadSummary
}

export async function getMappingUploadChoices(): Promise<{
  unique_employee_count: number
  hr_uploads: MappingUploadChoice[]
  economic_uploads: MappingUploadChoice[]
}> {
  const response = await fetch(`${API_BASE_URL}/temporal-mapping/uploads`)
  const body = await response.json().catch(() => ({})) as ApiErrorBody
  if (!response.ok) throw new UploadRequestError(body)
  return body as unknown as { hr_uploads: MappingUploadChoice[]; economic_uploads: MappingUploadChoice[]; unique_employee_count: number }
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

function module4Url(employeeId: string, action: 'recommendations' | 'simulation', uploadId?: string, demo = false): string {
  const url = `${API_BASE_URL}/module4/employees/${encodeURIComponent(employeeId)}/${action}`
  const params = new URLSearchParams()
  if (uploadId) params.set('upload_id', uploadId)
  if (demo) params.set('demo', 'true')
  return params.size ? `${url}?${params.toString()}` : url
}

function safeErrorDetail(detail: unknown): string | undefined {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && typeof detail[0]?.msg === 'string') return detail[0].msg
  return undefined
}

export async function getRetentionRecommendations(employeeId: string, uploadId?: string, demo = false): Promise<Module4RecommendationResponse> {
  let response: Response
  try {
    response = await fetch(module4Url(employeeId, 'recommendations', uploadId, demo))
  } catch {
    throw new RetentionRequestError(0, 'Unable to reach the backend. Confirm that the FastAPI server is running and try again.')
  }

  const body = await response.json().catch(() => ({})) as { detail?: unknown }
  if (!response.ok) {
    const fallbackMessages: Record<number, string> = {
      404: 'No employee was found with that employee ID.',
      409: 'This employee ID exists in more than one upload and cannot be selected unambiguously.',
      500: 'The backend encountered an unexpected error while preparing the employee analysis.',
      502: 'Module 4 could not load valid integration data for this employee.',
      503: 'A required Module 2 or Module 3 result is temporarily unavailable.',
    }
    throw new RetentionRequestError(
      response.status,
      safeErrorDetail(body.detail) ?? fallbackMessages[response.status] ?? 'The retention analysis request could not be completed.',
    )
  }
  return body as Module4RecommendationResponse
}

export async function simulateRetentionScenario(
  employeeId: string,
  changes: WhatIfChanges,
  uploadId?: string,
  demo = false,
): Promise<WhatIfSimulationResponse> {
  let response: Response
  try {
    response = await fetch(module4Url(employeeId, 'simulation', uploadId, demo), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(changes),
    })
  } catch {
    throw new RetentionRequestError(0, 'Unable to reach the backend. Confirm that the FastAPI server is running and try again.')
  }
  const body = await response.json().catch(() => ({})) as { detail?: unknown }
  if (!response.ok) {
    const detail = safeErrorDetail(body.detail)
    throw new RetentionRequestError(response.status, detail ?? 'The illustrative scenario could not be evaluated.')
  }
  return body as WhatIfSimulationResponse
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
  if (!response.ok) throw new UploadRequestError(body, response.status)
  return body as unknown as CleaningAnalysis
}

export async function removeMissingValues(uploadId: string): Promise<RemoveMissingResult> {
  const response = await fetch(`${API_BASE_URL}/data-cleaning/remove-missing`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ upload_id: uploadId }),
  })
  const body = await response.json().catch(() => ({})) as ApiErrorBody
  if (!response.ok) throw new UploadRequestError(body, response.status)
  return body as unknown as RemoveMissingResult
}

export type Module3Contract = {
  contract_version: string
  dataset_kind: string
  purpose: string
  feature_columns: string[]
  eesi: { column: string; formula_id_column: string; formula_version_column: string; supported_formula_ids: string[] }
}

export type Module3ModelStatus = {
  model_available: boolean
  dataset_kind: string
  message: string
  model_name?: string
  classes?: string[]
  feature_columns?: string[]
  eesi_integration?: { enabled?: boolean; column?: string; formula_id?: string | null; formula_version?: string | null }
}

export type Module3Prediction = {
  predicted_class: string
  class_probabilities: Record<string, number>
  interpretation: string
}

export type Module3FeatureRecord = { Age: number; MonthlyIncome: number; OverTime: string; JobSatisfaction: number; JobLevel: number; YearsAtCompany: number; Department: string; EESI: number }
export type Module3PilotRecord = { employee_id: string; month: string; record: Module3FeatureRecord }
export function getModule3PilotRecords(): Promise<{ records: Module3PilotRecord[]; formula_id: string }> {
  return module3Request('pilot-records')
}

export type Module3Evaluation = {
  metrics: Record<string, number | null>
  confusion_matrix: number[][]
  confusion_matrix_labels: string[]
  dataset_split: { method: string; train_rows: number; heldout_rows: number }
  limitations: string[]
}

async function module3Request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}/module3/${path}`, init)
  const body = await response.json().catch(() => ({})) as { detail?: string }
  if (!response.ok) throw new Error(body.detail ?? 'Module 3 request failed.')
  return body as T
}

export function getModule3Contract(): Promise<Module3Contract> {
  return module3Request<Module3Contract>('integration-contract')
}

export function getModule3ModelStatus(): Promise<Module3ModelStatus> {
  return module3Request<Module3ModelStatus>('prediction-status')
}

export function predictModule3(record: Record<string, string | number>): Promise<Module3Prediction> {
  return module3Request<Module3Prediction>('predict', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ record }),
  })
}

export function getModule3Evaluation(): Promise<Module3Evaluation> {
  return module3Request<Module3Evaluation>('evaluation')
}

export async function getIntegrationMappingRuns(): Promise<{ mapping_runs: IntegrationMappingRun[] }> {
  const response = await fetch(`${API_BASE_URL}/integration/mapping-runs`)
  const body = await response.json().catch(() => ({})) as ApiErrorBody
  if (!response.ok) throw new UploadRequestError(body)
  return body as unknown as { mapping_runs: IntegrationMappingRun[] }
}

export async function generateIntegratedDataset(mappingRunId: string): Promise<IntegrationResult> {
  const response = await fetch(`${API_BASE_URL}/integration/generate`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ temporal_mapping_run_id: mappingRunId }),
  })
  const body = await response.json().catch(() => ({})) as ApiErrorBody
  if (!response.ok) throw new UploadRequestError(body)
  return body as unknown as IntegrationResult
}

export async function getValidationIntegrationRuns(): Promise<{ integration_runs: ValidationIntegrationRun[] }> {
  const response = await fetch(`${API_BASE_URL}/dataset-validation/integration-runs`)
  const body = await response.json().catch(() => ({})) as ApiErrorBody
  if (!response.ok) throw new UploadRequestError(body)
  return body as unknown as { integration_runs: ValidationIntegrationRun[] }
}

export async function validateIntegratedDataset(integrationRunId: string): Promise<DatasetValidationReport> {
  const response = await fetch(`${API_BASE_URL}/dataset-validation/integration/${integrationRunId}`)
  const body = await response.json().catch(() => ({})) as ApiErrorBody
  if (!response.ok) throw new UploadRequestError(body)
  return body as unknown as DatasetValidationReport
}
