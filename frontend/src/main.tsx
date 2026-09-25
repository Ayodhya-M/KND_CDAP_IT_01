import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { useEffect, useState } from 'react'
import { createTemporalMappingPreview, getMappingUploadChoices, uploadHrDataset, uploadMacroeconomicDataset, type HrUploadSummary, type MacroUploadSummary, type MappingUploadChoice, type TemporalMappingPreview, UploadRequestError } from './api'
import './styles.css'

const stats = [
  ['Total Employees', '0', 'Employees will appear after HR upload.'],
  ['HR Records Uploaded', '0', 'No HR dataset uploaded yet.'],
  ['Economic Records Uploaded', '0', 'No economic dataset uploaded yet.'],
  ['Integration Status', 'Not started', 'Upload both datasets to begin.'],
]

function App() {
  return <Dashboard />
}

function Dashboard() {
  const [view, setView] = useState<'dashboard' | 'hr-upload' | 'macro-upload' | 'temporal-mapping'>('dashboard')
  const [totalEmployees, setTotalEmployees] = useState(0)
  const [hrUploads, setHrUploads] = useState(0)
  const [economicUploads, setEconomicUploads] = useState(0)

  const handleSuccessfulUpload = (summary: HrUploadSummary) => {
    setTotalEmployees(summary.valid_records ?? 0)
    setHrUploads((uploads) => uploads + 1)
  }

  return <main className="dashboard-layout">
    <aside className="sidebar"><div><p className="eyebrow">KND CDAP</p><h2>Research Hub</h2></div><nav><button className={view === 'dashboard' ? 'active' : ''} onClick={() => setView('dashboard')}>Dashboard</button><button className={view === 'hr-upload' ? 'active' : ''} onClick={() => setView('hr-upload')}>Upload HR data</button><button className={view === 'macro-upload' ? 'active' : ''} onClick={() => setView('macro-upload')}>Upload economic data</button><button className={view === 'temporal-mapping' ? 'active' : ''} onClick={() => setView('temporal-mapping')}>Temporal mapping</button><button disabled>Data validation</button><button disabled>Predictions</button></nav></aside>
    <section className="dashboard-content">
      {view === 'dashboard' ? <><header><div><p className="eyebrow">Overview</p><h1>HR & Economic Data Integration</h1><p className="muted">Your HR attrition analysis workspace is ready.</p></div><button className="primary-button compact" onClick={() => setView('hr-upload')}>Upload dataset</button></header>
      <div className="stats-grid">{stats.map(([label, value, detail]) => <article className="stat-card" key={label}><p>{label}</p><strong>{label === 'Total Employees' ? totalEmployees : label === 'HR Records Uploaded' ? hrUploads : label === 'Economic Records Uploaded' ? economicUploads : value}</strong><small>{detail}</small></article>)}</div>
      <section className="next-step"><div><p className="eyebrow">Get started</p><h2>Upload your HR dataset</h2><p>Use the Module 1 pilot CSV to validate employee records and their observation period.</p></div><button className="primary-button" onClick={() => setView('hr-upload')}>Upload HR dataset</button></section>
      <section className="activity"><h2>Workflow progress</h2><div className="progress-steps"><span className="current">1<br /><small>Upload</small></span><span>2<br /><small>Clean</small></span><span>3<br /><small>Map</small></span><span>4<br /><small>Predict</small></span></div></section></> : view === 'hr-upload' ? <HrUploadView onSuccess={handleSuccessfulUpload} /> : view === 'macro-upload' ? <MacroUploadView onSuccess={() => setEconomicUploads((uploads) => uploads + 1)} /> : <TemporalMappingView />}
    </section>
  </main>
}

function HrUploadView({ onSuccess }: { onSuccess: (summary: HrUploadSummary) => void }) {
  const [file, setFile] = useState<File | null>(null)
  const [summary, setSummary] = useState<HrUploadSummary | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const upload = async () => {
    if (!file) return
    setLoading(true)
    setError('')
    setSummary(null)
    try {
      const result = await uploadHrDataset(file)
      setSummary(result)
      onSuccess(result)
    } catch (caughtError) {
      if (caughtError instanceof UploadRequestError) {
        setSummary(caughtError.validationSummary)
        setError(caughtError.message)
      } else setError('Unable to upload the HR dataset. Confirm that the FastAPI backend is running.')
    } finally { setLoading(false) }
  }

  return <section className="upload-view"><p className="eyebrow">Module 1 · Step 1</p><h1>Upload HR dataset</h1><p className="muted">Choose a CSV containing the required HR fields, including <code>ObservationDate</code>.</p>
    <label className="file-picker"><span>Select CSV file</span><input type="file" accept=".csv,text/csv" onChange={(event) => { setFile(event.target.files?.[0] ?? null); setSummary(null); setError('') }} /></label>
    <p className="selected-file">{file ? `Selected: ${file.name}` : 'No file selected'}</p>
    <button className="primary-button" disabled={!file || loading} onClick={upload}>{loading ? 'Validating and saving…' : 'Upload dataset'}</button>
    {error && <p className="upload-error" role="alert">{error}</p>}
    {summary && <ValidationSummary summary={summary} />}
  </section>
}

function ValidationSummary({ summary }: { summary: HrUploadSummary }) {
  const missingValues = Object.entries(summary.missing_values ?? {}).filter(([, count]) => count > 0)
  return <section className={`validation-summary ${summary.status}`}><h2>{summary.status === 'success' ? 'Upload validated successfully' : 'Validation issues found'}</h2><div className="summary-grid"><span>Total Records<strong>{summary.total_records ?? 0}</strong></span><span>Valid Records<strong>{summary.valid_records ?? 0}</strong></span><span>Invalid Records<strong>{summary.invalid_records ?? 0}</strong></span><span>Duplicate Employee IDs<strong>{summary.duplicate_employee_ids ?? 0}</strong></span><span>Observation Period<strong>{summary.observation_period ? `${summary.observation_period.start} to ${summary.observation_period.end}` : '—'}</strong></span></div>
    <p><strong>Missing Values:</strong> {missingValues.length ? missingValues.map(([column, count]) => `${column}: ${count}`).join(', ') : 'None'}</p>
    {!!summary.errors?.length && <ul>{summary.errors.map((item, index) => <li key={`${item.field}-${index}`}><strong>{item.field}:</strong> {item.message}{item.count ? ` (${item.count} record(s))` : ''}</li>)}</ul>}
  </section>
}

function MacroUploadView({ onSuccess }: { onSuccess: (summary: MacroUploadSummary) => void }) {
  const [file, setFile] = useState<File | null>(null)
  const [summary, setSummary] = useState<MacroUploadSummary | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const upload = async () => {
    if (!file) return
    setLoading(true); setError(''); setSummary(null)
    try { const result = await uploadMacroeconomicDataset(file); setSummary(result); onSuccess(result) }
    catch (caughtError) {
      if (caughtError instanceof UploadRequestError) {
        const validation = caughtError.body as MacroUploadSummary
        if (validation.status === 'validation_failed') setSummary(validation)
        setError(caughtError.message)
      }
      else setError('Unable to upload the macroeconomic dataset. Confirm that the FastAPI backend is running.')
    } finally { setLoading(false) }
  }
  return <section className="upload-view"><p className="eyebrow">Module 1 · Step 2</p><h1>Upload macroeconomic data</h1><p className="muted">Choose monthly Sri Lankan macroeconomic data from January to June 2023.</p>
    <label className="file-picker"><span>Select CSV file</span><input type="file" accept=".csv,text/csv" onChange={(event) => { setFile(event.target.files?.[0] ?? null); setSummary(null); setError('') }} /></label>
    <p className="selected-file">{file ? `Selected: ${file.name}` : 'No file selected'}</p><button className="primary-button" disabled={!file || loading} onClick={upload}>{loading ? 'Validating and saving…' : 'Upload dataset'}</button>
    {error && <p className="upload-error" role="alert">{error}</p>}{summary && <MacroValidationSummary summary={summary} />}
  </section>
}

function MacroValidationSummary({ summary }: { summary: MacroUploadSummary }) {
  const missingValues = Object.entries(summary.missing_values ?? {}).filter(([, count]) => count > 0)
  return <section className={`validation-summary ${summary.status}`}><h2>{summary.status === 'success' ? 'Upload validated successfully' : 'Validation issues found'}</h2><div className="summary-grid"><span>Total Records<strong>{summary.total_records ?? 0}</strong></span><span>Valid Records<strong>{summary.valid_records ?? 0}</strong></span><span>Invalid Records<strong>{summary.invalid_records ?? 0}</strong></span><span>Duplicate Months<strong>{summary.duplicate_months ?? 0}</strong></span><span>Economic Period<strong>{summary.economic_period ? `${summary.economic_period.start} to ${summary.economic_period.end}` : '—'}</strong></span></div><p><strong>Missing Values:</strong> {missingValues.length ? missingValues.map(([column, count]) => `${column}: ${count}`).join(', ') : 'None'}</p>{!!summary.errors?.length && <ul>{summary.errors.map((item, index) => <li key={`${item.field}-${index}`}><strong>{item.field}:</strong> {item.message}{item.count ? ` (${item.count} record(s))` : ''}</li>)}</ul>}</section>
}

function TemporalMappingView() {
  const [hrUploads, setHrUploads] = useState<MappingUploadChoice[]>([])
  const [economicUploads, setEconomicUploads] = useState<MappingUploadChoice[]>([])
  const [hrUploadId, setHrUploadId] = useState('')
  const [economicUploadId, setEconomicUploadId] = useState('')
  const [preview, setPreview] = useState<TemporalMappingPreview | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [mapping, setMapping] = useState(false)

  useEffect(() => {
    const loadUploads = async () => {
      setLoading(true)
      try {
        const choices = await getMappingUploadChoices()
        setHrUploads(choices.hr_uploads)
        setEconomicUploads(choices.economic_uploads)
        setHrUploadId((current) => current || choices.hr_uploads[0]?.id || '')
        setEconomicUploadId((current) => current || choices.economic_uploads[0]?.id || '')
      } catch (caughtError) {
        setError(caughtError instanceof Error ? caughtError.message : 'Unable to load the uploaded datasets.')
      } finally { setLoading(false) }
    }
    void loadUploads()
  }, [])

  const createPreview = async () => {
    if (!hrUploadId || !economicUploadId) return
    setMapping(true); setError(''); setPreview(null)
    try { setPreview(await createTemporalMappingPreview(hrUploadId, economicUploadId)) }
    catch (caughtError) { setError(caughtError instanceof Error ? caughtError.message : 'Unable to create the temporal mapping preview.') }
    finally { setMapping(false) }
  }

  return <section className="upload-view mapping-view"><p className="eyebrow">Module 1 · Step 3</p><h1>Temporal-contextual mapping</h1><p className="muted">Each employee is matched to the economic indicators for the month of their <code>ObservationDate</code>.</p>
    {loading ? <p className="muted">Loading uploaded datasets…</p> : <><div className="mapping-selects"><label>HR dataset<select value={hrUploadId} onChange={(event) => setHrUploadId(event.target.value)}><option value="">Select HR upload</option>{hrUploads.map((upload) => <option key={upload.id} value={upload.id}>{upload.original_filename} ({upload.record_count} records)</option>)}</select></label><label>Macroeconomic dataset<select value={economicUploadId} onChange={(event) => setEconomicUploadId(event.target.value)}><option value="">Select economic upload</option>{economicUploads.map((upload) => <option key={upload.id} value={upload.id}>{upload.original_filename} ({upload.record_count} months)</option>)}</select></label></div><button className="primary-button" disabled={!hrUploadId || !economicUploadId || mapping} onClick={createPreview}>{mapping ? 'Creating mapping preview…' : 'Create mapping preview'}</button></>}
    {error && <p className="upload-error" role="alert">{error}</p>}
    {preview && <section className="validation-summary success"><h2>Mapping preview created</h2><div className="summary-grid"><span>Employee Records<strong>{preview.total_employee_records}</strong></span><span>Matched Records<strong>{preview.matched_records}</strong></span><span>Unmatched Records<strong>{preview.unmatched_records}</strong></span><span>Mapping Rate<strong>{preview.mapping_rate}%</strong></span></div><div className="mapping-table-wrap"><table><thead><tr><th>Employee ID</th><th>Observation Date</th><th>Economic Month</th><th>Status</th></tr></thead><tbody>{preview.mappings.map((row) => <tr key={row.employee_id}><td>{row.employee_id}</td><td>{row.observation_date ?? '—'}</td><td>{row.economic_month ?? '—'}</td><td><span className={`mapping-status ${row.status}`}>{row.status}</span></td></tr>)}</tbody></table></div></section>}
  </section>
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
