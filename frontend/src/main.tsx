import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { useEffect, useState } from 'react'
import { analyseMissingValues, createTemporalMappingPreview, getCleaningUploadChoices, getMappingUploadChoices, getModule3ModelStatus, removeMissingValues, uploadHrDataset, uploadMacroeconomicDataset, type CleaningAnalysis, type CleaningUploadChoice, type HrUploadSummary, type MacroUploadSummary, type MappingUploadChoice, type Module3ModelStatus, type RemoveMissingResult, type TemporalMappingPreview, UploadRequestError } from './api'
import './styles.css'
import EesiView from './EesiView'
import Module3View from './Module3View'
import { Module4Dashboard } from './pages/Module4Dashboard'
import { Icon, type IconName } from './components/Icon'

type View = 'dashboard' | 'hr-upload' | 'macro-upload' | 'data-cleaning' | 'temporal-mapping' | 'eesi' | 'module3' | 'module4'

const viewDetails: Record<View, { section: string; title: string }> = {
  dashboard: { section: 'Workspace', title: 'Executive overview' },
  'hr-upload': { section: 'Data Management', title: 'HR datasets' },
  'macro-upload': { section: 'Data Management', title: 'Economic datasets' },
  'data-cleaning': { section: 'Data Management', title: 'Data quality' },
  'temporal-mapping': { section: 'Data Management', title: 'Temporal mapping' },
  eesi: { section: 'Economic Intelligence', title: 'Economic pressure analysis' },
  module3: { section: 'Turnover Analytics', title: 'Prediction workspace' },
  module4: { section: 'Retention Strategies', title: 'Decision support' },
}

function App() {
  return <Dashboard />
}

function Dashboard() {
  const [view, setView] = useState<View>('dashboard')
  const [mobileNavOpen, setMobileNavOpen] = useState(false)
  const [hrUploads, setHrUploads] = useState<MappingUploadChoice[]>([])
  const [economicUploads, setEconomicUploads] = useState<MappingUploadChoice[]>([])
  const [modelStatus, setModelStatus] = useState<Module3ModelStatus | null>(null)
  const [overviewError, setOverviewError] = useState('')
  const [overviewLoading, setOverviewLoading] = useState(true)

  const refreshOverview = async () => {
    setOverviewLoading(true)
    setOverviewError('')
    const [uploadsResult, modelResult] = await Promise.allSettled([getMappingUploadChoices(), getModule3ModelStatus()])
    if (uploadsResult.status === 'fulfilled') {
      setHrUploads(uploadsResult.value.hr_uploads)
      setEconomicUploads(uploadsResult.value.economic_uploads)
    }
    if (modelResult.status === 'fulfilled') setModelStatus(modelResult.value)
    if (uploadsResult.status === 'rejected' || modelResult.status === 'rejected') setOverviewError('Some live workspace status could not be loaded. Available information is shown below.')
    setOverviewLoading(false)
  }

  useEffect(() => { void refreshOverview() }, [])

  const handleSuccessfulUpload = (summary: HrUploadSummary) => {
    if (summary.status === 'success') void refreshOverview()
  }

  const navigate = (next: View) => { setView(next); setMobileNavOpen(false) }
  const current = viewDetails[view]

  return <main className="dashboard-layout">
    <aside className={`sidebar ${mobileNavOpen ? 'open' : ''}`}>
      <div className="app-brand">
        <img className="app-brand-icon" src="/retention-intelligence-favicon.svg" alt="Retention Intelligence" />
        <div><h2>Retention Intelligence</h2><p>Workforce Analytics &amp; Decision Support</p></div>
      </div>
      <nav aria-label="Research modules">
        <button className={view === 'dashboard' ? 'active' : ''} onClick={() => navigate('dashboard')}><Icon name="overview" /><span>Overview</span></button>
        <p className="nav-label">Research workspaces</p>
        <button className={['hr-upload','macro-upload','data-cleaning','temporal-mapping'].includes(view) ? 'active' : ''} onClick={() => navigate('hr-upload')}><Icon name="database" /><span>Data Management</span></button>
        <div className="nav-subitems">
          <button className={view === 'macro-upload' ? 'active' : ''} onClick={() => navigate('macro-upload')}>Economic uploads</button>
          <button className={view === 'data-cleaning' ? 'active' : ''} onClick={() => navigate('data-cleaning')}>Data quality</button>
          <button className={view === 'temporal-mapping' ? 'active' : ''} onClick={() => navigate('temporal-mapping')}>Temporal mapping</button>
        </div>
        <button className={view === 'eesi' ? 'active' : ''} onClick={() => navigate('eesi')}><Icon name="economy" /><span>Economic Intelligence</span></button>
        <button className={view === 'module3' ? 'active' : ''} onClick={() => navigate('module3')}><Icon name="prediction" /><span>Turnover Analytics</span></button>
        <button className={view === 'module4' ? 'active' : ''} onClick={() => navigate('module4')}><Icon name="retention" /><span>Retention Strategies</span></button>
      </nav>
      <div className="sidebar-footer"><span className="system-dot" aria-hidden="true" /><div><strong>Research environment</strong><small>Decision support prototype</small></div></div>
    </aside>
    <section className="dashboard-content">
      <div className="topbar"><button className="mobile-menu" type="button" aria-label="Toggle navigation" aria-expanded={mobileNavOpen} onClick={() => setMobileNavOpen(value => !value)}><Icon name="menu" /></button><img className="topbar-brand-icon" src="/retention-intelligence-favicon.svg" alt="" aria-hidden="true" /><div><p className="breadcrumb">Retention Intelligence <span>/</span> {current.section}</p><h1>{current.title}</h1></div><span className="topbar-context">Research prototype</span></div>
      <div className="page-content">
      {view === 'dashboard' ? <OverviewDashboard hrUploads={hrUploads} economicUploads={economicUploads} modelStatus={modelStatus} loading={overviewLoading} error={overviewError} onNavigate={navigate} onRefresh={() => void refreshOverview()} /> : view === 'hr-upload' ? <HrUploadView onSuccess={handleSuccessfulUpload} /> : view === 'macro-upload' ? <MacroUploadView onSuccess={() => void refreshOverview()} /> : view === 'data-cleaning' ? <DataCleaningView /> : view === 'temporal-mapping' ? <TemporalMappingView /> : view === 'eesi' ? <EesiView /> : view === 'module3' ? <Module3View /> : <Module4Dashboard />}
      </div>
    </section>
  </main>
}

function OverviewDashboard({ hrUploads, economicUploads, modelStatus, loading, error, onNavigate, onRefresh }: { hrUploads: MappingUploadChoice[]; economicUploads: MappingUploadChoice[]; modelStatus: Module3ModelStatus | null; loading: boolean; error: string; onNavigate: (view: View) => void; onRefresh: () => void }) {
  const hrRecords = hrUploads.reduce((total, upload) => total + upload.record_count, 0)
  const recent = [...hrUploads.map(item => ({ ...item, type: 'HR dataset' })), ...economicUploads.map(item => ({ ...item, type: 'Economic dataset' }))].sort((a, b) => Date.parse(b.uploaded_at) - Date.parse(a.uploaded_at)).slice(0, 5)
  const workspaces: Array<{ view: View; icon: IconName; title: string; detail: string; status: string }> = [
    { view: 'hr-upload', icon: 'database', title: 'Data Management', detail: 'Upload, validate, clean and temporally map workforce data.', status: `${hrUploads.length + economicUploads.length} datasets` },
    { view: 'eesi', icon: 'economy', title: 'Economic Intelligence', detail: 'Explore economic exposure formulas and reference profiles.', status: economicUploads.length ? 'Data available' : 'Awaiting data' },
    { view: 'module3', icon: 'prediction', title: 'Turnover Analytics', detail: 'Review model availability and the prediction contract.', status: modelStatus?.model_available ? 'Model available' : 'Model unavailable' },
    { view: 'module4', icon: 'retention', title: 'Retention Strategies', detail: 'Generate explainable, prioritized HR decision support.', status: 'Prototype available' },
  ]
  return <section className="overview-dashboard">
    <header className="overview-brand-header"><div className="overview-brand-copy"><img className="overview-full-logo" src="/retention-intelligence-logo.png" alt="Retention Intelligence" /><p>Monitor workforce data readiness and move between the four connected research modules.</p></div><button className="secondary-button" onClick={onRefresh}>Refresh status</button></header>
    {error && <div className="inline-alert" role="alert"><span>{error}</span><button className="text-button" onClick={onRefresh}>Retry</button></div>}
    {loading && <div className="overview-skeleton" role="status" aria-label="Loading workspace status">{[1,2,3,4].map(item => <span key={item} />)}</div>}
    {!loading && <>
    <div className="executive-metrics">
      <article><span>HR records available</span><strong>{hrRecords.toLocaleString()}</strong><small>Across {hrUploads.length} uploaded dataset{hrUploads.length === 1 ? '' : 's'}; duplicates are not deduplicated.</small></article>
      <article><span>Dataset inventory</span><strong>{hrUploads.length + economicUploads.length}</strong><small>{hrUploads.length} HR · {economicUploads.length} economic</small></article>
      <article><span>Turnover model</span><strong className="metric-text">{modelStatus?.model_available ? 'Available' : 'Unavailable'}</strong><small>{modelStatus?.message ?? 'Status has not been loaded.'}</small></article>
      <article><span>Retention support</span><strong className="metric-text">Prototype</strong><small>Mock Module 2/3 providers remain clearly identified.</small></article>
    </div>
    <div className="overview-grid">
      <section className="workspace-panel"><div className="panel-heading"><div><p className="eyebrow">Research modules</p><h3>Analysis workspaces</h3></div></div><div className="workspace-list">{workspaces.map(item => <button key={item.view} onClick={() => onNavigate(item.view)}><span className="workspace-icon"><Icon name={item.icon} /></span><span><strong>{item.title}</strong><small>{item.detail}</small></span><span className="workspace-status">{item.status}</span><Icon name="arrow" className="row-arrow" /></button>)}</div></section>
      <section className="activity-panel"><div className="panel-heading"><div><p className="eyebrow">Data operations</p><h3>Recent dataset activity</h3></div><button className="text-button" onClick={() => onNavigate('hr-upload')}>Manage data</button></div>{recent.length ? <div className="activity-list">{recent.map(item => <div key={item.id}><span className="file-icon"><Icon name="database" /></span><span><strong>{item.original_filename}</strong><small>{item.type} · {item.record_count.toLocaleString()} records</small></span><time dateTime={item.uploaded_at}>{new Date(item.uploaded_at).toLocaleDateString()}</time></div>)}</div> : <div className="professional-empty"><Icon name="database" /><strong>No datasets available</strong><p>Upload HR and economic datasets to begin the integrated workflow.</p><button className="primary-button" onClick={() => onNavigate('hr-upload')}>Upload a dataset</button></div>}</section>
    </div>
    </>}
  </section>
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

  return <section className="upload-view"><h1>Upload HR dataset</h1><p className="muted">Choose a CSV containing the required HR fields, including <code>ObservationDate</code>.</p>
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
  return <section className="upload-view"><h1>Upload macroeconomic data</h1><p className="muted">Choose monthly Sri Lankan macroeconomic data from January to June 2023.</p>
    <label className="file-picker"><span>Select CSV file</span><input type="file" accept=".csv,text/csv" onChange={(event) => { setFile(event.target.files?.[0] ?? null); setSummary(null); setError('') }} /></label>
    <p className="selected-file">{file ? `Selected: ${file.name}` : 'No file selected'}</p><button className="primary-button" disabled={!file || loading} onClick={upload}>{loading ? 'Validating and saving…' : 'Upload dataset'}</button>
    {error && <p className="upload-error" role="alert">{error}</p>}{summary && <MacroValidationSummary summary={summary} />}
  </section>
}

function MacroValidationSummary({ summary }: { summary: MacroUploadSummary }) {
  const missingValues = Object.entries(summary.missing_values ?? {}).filter(([, count]) => count > 0)
  return <section className={`validation-summary ${summary.status}`}><h2>{summary.status === 'success' ? 'Upload validated successfully' : 'Validation issues found'}</h2><div className="summary-grid"><span>Total Records<strong>{summary.total_records ?? 0}</strong></span><span>Valid Records<strong>{summary.valid_records ?? 0}</strong></span><span>Invalid Records<strong>{summary.invalid_records ?? 0}</strong></span><span>Duplicate Months<strong>{summary.duplicate_months ?? 0}</strong></span><span>Economic Period<strong>{summary.economic_period ? `${summary.economic_period.start} to ${summary.economic_period.end}` : '—'}</strong></span></div><p><strong>Missing Values:</strong> {missingValues.length ? missingValues.map(([column, count]) => `${column}: ${count}`).join(', ') : 'None'}</p>{!!summary.errors?.length && <ul>{summary.errors.map((item, index) => <li key={`${item.field}-${index}`}><strong>{item.field}:</strong> {item.message}{item.count ? ` (${item.count} record(s))` : ''}</li>)}</ul>}</section>
}

function DataCleaningView() {
  const [uploads, setUploads] = useState<CleaningUploadChoice[]>([])
  const [uploadId, setUploadId] = useState('')
  const [analysis, setAnalysis] = useState<CleaningAnalysis | null>(null)
  const [result, setResult] = useState<RemoveMissingResult | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [cleaning, setCleaning] = useState(false)

  useEffect(() => {
    const loadUploads = async () => {
      try {
        const response = await getCleaningUploadChoices()
        setUploads(response.uploads)
        setUploadId((current) => current || response.uploads[0]?.id || '')
      } catch (caughtError) {
        setError(caughtError instanceof Error ? caughtError.message : 'Unable to load uploaded datasets.')
      } finally { setLoading(false) }
    }
    void loadUploads()
  }, [])

  const analyse = async () => {
    if (!uploadId) return
    setCleaning(true); setError(''); setAnalysis(null); setResult(null)
    try { setAnalysis(await analyseMissingValues(uploadId)) }
    catch (caughtError) { setError(caughtError instanceof Error ? caughtError.message : 'Unable to analyse missing values.') }
    finally { setCleaning(false) }
  }

  const removeMissing = async () => {
    if (!uploadId) return
    setCleaning(true); setError(''); setResult(null)
    try { setResult(await removeMissingValues(uploadId)) }
    catch (caughtError) { setError(caughtError instanceof Error ? caughtError.message : 'Unable to remove missing values.') }
    finally { setCleaning(false) }
  }

  const missingEntries = Object.entries(analysis?.missing_values ?? {})
  return <section className="upload-view"><h1>Data cleaning</h1><p className="muted">Analyse an uploaded dataset, then remove records with missing required values. The original uploaded dataset is never deleted.</p>
    {loading ? <p className="muted">Loading uploaded datasets…</p> : <><div className="cleaning-controls"><label>Dataset to clean<select value={uploadId} onChange={(event) => { setUploadId(event.target.value); setAnalysis(null); setResult(null) }}><option value="">Select an upload</option>{uploads.map((upload) => <option key={upload.id} value={upload.id}>{upload.dataset_type === 'hr' ? 'HR' : 'Economic'} — {upload.original_filename} ({upload.record_count} records)</option>)}</select></label><div className="cleaning-buttons"><button className="secondary-button" disabled={!uploadId || cleaning} onClick={analyse}>{cleaning ? 'Working…' : 'Analyse missing values'}</button><button className="primary-button" disabled={!uploadId || cleaning} onClick={removeMissing}>{cleaning ? 'Working…' : 'Remove missing values'}</button></div></div></>}
    {error && <p className="upload-error" role="alert">{error}</p>}
    {analysis && <section className="validation-summary success"><h2>Missing-value analysis</h2><div className="summary-grid"><span>Total Records<strong>{analysis.total_records}</strong></span><span>Rows With Missing Values<strong>{analysis.rows_with_missing_values}</strong></span></div><p><strong>Missing Values:</strong> {missingEntries.length ? missingEntries.map(([field, count]) => `${field}: ${count}`).join(', ') : 'None'}</p>{analysis.sample_row_numbers.length > 0 && <p><strong>Sample source rows:</strong> {analysis.sample_row_numbers.join(', ')}</p>}</section>}
    {result && <section className="validation-summary success"><h2>Cleaning completed</h2><div className="summary-grid"><span>Rows Before<strong>{result.rows_before}</strong></span><span>Rows After<strong>{result.rows_after}</strong></span><span>Removed Records<strong>{result.removed_records}</strong></span></div><p>{result.message}</p></section>}
  </section>
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
