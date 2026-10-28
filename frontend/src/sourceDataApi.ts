const API = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'
export type SourceDataset = {
  id: string; name: string; kind: string; currency: string; target: string; target_label: string
  source_file: string; source_rows: number; record_count: number; model_available: boolean
  eesi_available: boolean; warning: string; date_note: string; eesi_note: string; retained_fields: string[]
  split: { train_rows: number; heldout_rows: number }
}
export type SourceAnalysis = {
  dataset: SourceDataset; record_id: string; inputs: Record<string, number | string>
  eesi: { scores: Record<string, number>; version: string; warnings: string[] } | null
  prediction: { predicted_class: string; class_probabilities: Record<string, number>; target_label: string }
  recommendations: { title: string; sensitivity_pp: number; note: string }[]
  evaluation: { split: { train_rows: number; heldout_rows: number }; metrics: Record<string, number | null> }
  limitations: string[]; scenario: boolean; saved_records_unchanged: boolean
}
async function request<T>(path: string, body?: object): Promise<T> {
  const response = await fetch(`${API}/source-data${path}`, body ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) } : undefined)
  const result = await response.json()
  if (!response.ok) throw new Error(typeof result.detail === 'string' ? result.detail : 'Source analysis could not be completed.')
  return result as T
}
export const getSources = () => request<{ datasets: SourceDataset[] }>('')
export const getSourceRecords = (id: string) => request<{ records: { record_id: string; month: string | null }[] }>(`/${encodeURIComponent(id)}/records`)
export const analyseSource = (id: string, record: string, salary?: number) => request<SourceAnalysis>(`/${encodeURIComponent(id)}/records/${encodeURIComponent(record)}/analyse`, salary === undefined ? {} : { salary })
