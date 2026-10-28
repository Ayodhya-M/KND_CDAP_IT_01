import { useEffect, useState, type CSSProperties } from 'react'
import { getMappingUploadChoices, getRetentionRecommendations, RetentionRequestError, type MappingUploadChoice, type Module4RecommendationResponse, type WhatIfSimulationResponse } from '../api'
import { EmployeeSearch } from '../components/EmployeeSearch'
import { EmptyRecommendations } from '../components/EmptyRecommendations'
import { IntegrationStatus } from '../components/IntegrationStatus'
import { RecommendationCard } from '../components/RecommendationCard'
import { RetentionActionPlan } from '../components/RetentionActionPlan'
import { formatFeatureName } from '../components/RiskFactorsList'
import { WhatIfSimulator } from '../components/WhatIfSimulator'

function displayValue(value: unknown) {
  if (value === null || value === undefined || value === '') return 'Not available'
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  return String(value)
}

function priorityClass(level: string) {
  const normalized = level.toLowerCase()
  return ['low', 'medium', 'high'].includes(normalized) ? normalized : 'neutral'
}

function PriorityRing({ score, level }: { score: number; level: string }) {
  const style = { '--priority-angle': `${Math.max(0, Math.min(score, 100)) * 3.6}deg` } as CSSProperties
  return <div className="priority-ring-wrap">
    <div className="priority-ring" style={style} role="img" aria-label={`Recommendation priority score ${score.toFixed(1)} out of 100`}><div><strong>{score.toFixed(1)}</strong><span>/ 100</span></div></div>
    <div><span className={`status-badge ${priorityClass(level)}`}>{level} priority</span><p>Prototype action-ranking score</p></div>
  </div>
}

function ScenarioPreview({ result }: { result: WhatIfSimulationResponse | null }) {
  if (!result) return <div className="analytics-empty"><strong>No scenario compared yet</strong><p>Use the scenario planner below to compare supported temporary values.</p><a href="#what-if-heading">Open scenario planner</a></div>
  return <div className="scenario-preview">
    <div><span>Current</span><strong>{(result.original_turnover_probability * 100).toFixed(2)}%</strong></div><span aria-hidden="true">→</span><div><span>Scenario</span><strong>{(result.simulated_turnover_probability * 100).toFixed(2)}%</strong></div>
    <p><strong>{result.probability_difference > 0 ? '+' : ''}{result.probability_difference.toFixed(4)} pp</strong> model-based difference</p>
  </div>
}

export function Module4Dashboard() {
  const [employeeId, setEmployeeId] = useState('')
  const [result, setResult] = useState<Module4RecommendationResponse | null>(null)
  const [scenarioResult, setScenarioResult] = useState<WhatIfSimulationResponse | null>(null)
  const [validationError, setValidationError] = useState('')
  const [requestError, setRequestError] = useState('')
  const [loading, setLoading] = useState(false)
  const [uploads, setUploads] = useState<MappingUploadChoice[]>([])
  const [uploadId, setUploadId] = useState('')
  const [uploadsLoading, setUploadsLoading] = useState(true)
  const [uploadsError, setUploadsError] = useState('')
  const [demo, setDemo] = useState(true)

  const clearAnalysis = () => { setResult(null); setScenarioResult(null) }

  const loadUploads = async () => {
    setUploadsLoading(true); setUploadsError('')
    try {
      const response = await getMappingUploadChoices()
      setUploads(response.hr_uploads)
      setUploadId((current) => response.hr_uploads.some((upload) => upload.id === current) ? current : response.hr_uploads.find((upload) => upload.record_count === 300)?.id ?? '')
    } catch {
      setUploads([]); setUploadId('')
      setUploadsError('HR dataset uploads could not be loaded. Confirm that the backend is available, then retry.')
    } finally { setUploadsLoading(false) }
  }

  useEffect(() => { void loadUploads() }, [])

  const analyzeEmployee = async () => {
    const normalizedId = employeeId.trim()
    setValidationError(''); setRequestError(''); clearAnalysis()
    if (!normalizedId) { setValidationError('Enter an employee ID before starting the analysis.'); return }
    if (!uploadId) { setValidationError('Select an HR dataset before starting the analysis.'); return }
    setLoading(true)
    try {
      setResult(await getRetentionRecommendations(normalizedId, uploadId, demo))
      setEmployeeId(normalizedId)
    } catch (error) {
      setRequestError(error instanceof RetentionRequestError ? error.message : 'An unexpected error occurred while loading the retention analysis.')
    } finally { setLoading(false) }
  }

  const selectedUpload = uploads.find((upload) => upload.id === uploadId)
  const topRecommendation = result?.recommendations[0]
  const maxSensitivity = result ? Math.max(...result.important_risk_factors.map((factor) => Math.abs(factor.contribution)), 0.0001) : 1

  return <section className="module4-dashboard module4-analytics-dashboard">
    <header className="module4-analytics-header">
      <div><p className="module4-product-name">RETENTION INTELLIGENCE</p><h1>Retention Strategies</h1><p>HR DECISION SUPPORT</p></div>
      <div className="module4-header-controls">
        <span className="connected-pilot-indicator"><i aria-hidden="true" />{demo ? 'Connected Synthetic Pilot' : 'Configured Provider Mode'}</span>
        <label>Analysis mode<select disabled={loading} value={demo ? 'pilot' : 'configured'} onChange={(event) => { setDemo(event.target.value === 'pilot'); clearAnalysis(); setRequestError('') }}><option value="pilot">Connected Synthetic Pilot</option><option value="configured">Configured Providers</option></select></label>
      </div>
    </header>

    <div className="module4-pilot-notice" role="note"><strong>{demo ? 'Synthetic research environment.' : 'Development provider environment.'}</strong> {demo ? 'Probabilities use the saved pilot model; risk bands remain unclassified and sensitivities are not SHAP values or causal effects.' : 'Outputs use the explicitly configured providers and retain their API provenance. No automatic fallback is performed by the dashboard.'}</div>

    <section className="module4-search-strip" aria-labelledby="module4-search-heading">
      <div className="search-strip-title"><span>01</span><div><p>Employee analysis</p><h2 id="module4-search-heading">Select an employee record</h2></div></div>
      <div className="module4-dataset-picker">
        <label htmlFor="module4-upload">HR dataset</label>
        {uploadsLoading ? <p className="muted" role="status">Loading HR datasets…</p> : uploadsError ? <div className="dataset-load-error" role="alert"><span>{uploadsError}</span><button className="secondary-button" type="button" onClick={() => void loadUploads()}>Retry</button></div> : uploads.length === 0 ? <p className="muted">No HR datasets are available.</p> : <><select disabled={loading} id="module4-upload" title={selectedUpload?.original_filename} value={uploadId} onChange={(event) => { setUploadId(event.target.value); clearAnalysis(); setRequestError(''); setValidationError('') }}><option value="">Select an HR dataset</option>{uploads.map((upload) => <option key={upload.id} value={upload.id}>{upload.original_filename}</option>)}</select>{selectedUpload && <div className="dataset-metadata"><span><strong>{selectedUpload.record_count.toLocaleString()}</strong> records</span><span>Uploaded {new Date(selectedUpload.uploaded_at).toLocaleDateString()}</span></div>}</>}
      </div>
      <EmployeeSearch employeeId={employeeId} loading={loading} validationError={validationError} onEmployeeIdChange={(value) => { setEmployeeId(value); setValidationError(''); clearAnalysis() }} onSubmit={() => void analyzeEmployee()} />
    </section>

    {loading && <div className="analysis-loading" role="status" aria-live="polite"><span className="loading-indicator" aria-hidden="true" /><div><strong>Preparing retention analysis</strong><p>Loading employee context, calculating EESI, and requesting the selected prediction provider…</p></div></div>}
    {requestError && <div className="retention-error" role="alert"><strong>Analysis could not be completed</strong><p>{requestError}</p><small>Check the selected upload, employee ID, model availability, or backend connection, then try again.</small></div>}
    {!result && !loading && !requestError && <div className="module4-dashboard-empty"><strong>Employee analytics will appear here</strong><p>Select an HR dataset and analyze an employee to load live Module 4 pilot outputs.</p></div>}

    {result && <div className="module4-analytics-results">
      <section className="module4-kpi-grid" aria-label="Employee retention summary">
        <article className="module4-kpi blue"><span>Pilot Employees</span><strong>{selectedUpload?.record_count.toLocaleString() ?? '—'}</strong><small>Selected HR dataset</small></article>
        <article className="module4-kpi red"><span>Turnover Probability</span><strong>{(result.turnover_probability * 100).toFixed(2)}%</strong><small>{demo ? 'Synthetic model estimate' : result.metadata.module3_source} · {result.risk_level}</small></article>
        <article className="module4-kpi orange"><span>Economic Pressure (EESI)</span><strong>{result.eesi_score.toFixed(2)}</strong><small>{demo ? 'Exploratory Module 2 calculation' : result.metadata.module2_source}</small></article>
        <article className="module4-kpi green"><span>Retention Recommendations</span><strong>{result.recommendations.length}</strong><small>{topRecommendation ? `Top: ${topRecommendation.title}` : 'No supported action generated'}</small></article>
      </section>

      <section className="module4-analytics-grid" aria-label="Retention analytics">
        <article className="module4-analytics-panel priority-panel"><header><div><p>Action ranking</p><h2>Recommendation Priority</h2></div></header>{topRecommendation ? <><PriorityRing score={topRecommendation.priority_score} level={topRecommendation.priority_level} /><p className="panel-footnote">Top-ranked action: <strong>{topRecommendation.title}</strong></p></> : <div className="analytics-empty"><strong>No priority available</strong><p>No recommendation was generated for the current supported factors.</p></div>}</article>

        <article className="module4-analytics-panel sensitivities-panel"><header><div><p>Model diagnostics</p><h2>{demo ? 'Positive Input Sensitivities' : 'Important Risk Factors'}</h2></div><span>{result.important_risk_factors.length}</span></header>{result.important_risk_factors.length === 0 ? <div className="analytics-empty"><strong>No positive factor returned</strong></div> : <div className="sensitivity-bars">{result.important_risk_factors.map((factor, index) => { const value = factor.contribution * (demo ? 100 : 1); return <div key={`${factor.feature_name}-${index}`}><div><strong>{formatFeatureName(factor.feature_name)}</strong><span>{value.toFixed(2)}{demo ? ' pp' : ''}</span></div><div className="sensitivity-track"><i style={{ width: `${Math.max(4, Math.abs(factor.contribution) / maxSensitivity * 100)}%` }} /></div><small>Current value: {displayValue(factor.feature_value)}</small></div> })}</div>}<p className="panel-footnote">{demo ? 'One-feature input sensitivity in percentage points; not SHAP or causal attribution.' : 'Provider-supplied contribution values; consult the active provider disclaimer for interpretation.'}</p></article>

        <article className="module4-analytics-panel actions-panel"><header><div><p>Ranked interventions</p><h2>Recommended Retention Actions</h2></div><span>{result.recommendations.length}</span></header>{result.recommendations.length === 0 ? <EmptyRecommendations /> : <ol className="compact-action-list">{result.recommendations.map((recommendation, index) => <li key={recommendation.recommendation_id}><span>{index + 1}</span><div><strong>{recommendation.title}</strong><small>{formatFeatureName(recommendation.related_factor)}</small></div><div><strong>{recommendation.priority_score.toFixed(1)}</strong><small>{recommendation.priority_level}</small></div></li>)}</ol>}<a className="panel-link" href="#full-recommendations">View recommendation details</a></article>

        <article className="module4-analytics-panel scenario-panel"><header><div><p>Hypothetical comparison</p><h2>What-if Scenario Comparison</h2></div></header><ScenarioPreview result={scenarioResult} /><p className="panel-footnote">Model-based scenario only; no employee record is changed.</p></article>
      </section>

      <RetentionActionPlan recommendations={result.recommendations} />

      <section className="module4-detail-stack" aria-label="Detailed analysis">
        <details><summary><span>Detailed Employee Information</span><small>{result.employee_id}</small></summary><div className="detail-content"><div className="provenance-pills"><span>Module 1 · Database record</span><span>Module 2 · {result.metadata.module2_source}</span><span>Module 3 · {result.metadata.module3_source}</span></div><dl className="employee-profile-grid"><div><dt>Employee ID</dt><dd>{result.employee_id}</dd></div><div><dt>Department</dt><dd>{displayValue(result.employee_profile.department)}</dd></div><div><dt>Job role</dt><dd>{displayValue(result.employee_profile.job_role)}</dd></div><div><dt>Job level</dt><dd>{displayValue(result.employee_profile.job_level)}</dd></div><div><dt>Years at company</dt><dd>{displayValue(result.employee_profile.years_at_company)}</dd></div><div><dt>Overtime</dt><dd>{displayValue(result.employee_profile.overtime)}</dd></div><div><dt>Job satisfaction</dt><dd>{displayValue(result.employee_profile.job_satisfaction)}</dd></div><div><dt>Work-life balance</dt><dd>{displayValue(result.employee_profile.work_life_balance)}</dd></div></dl></div></details>

        <details id="full-recommendations" open><summary><span>Full Retention Recommendations</span><small>Priority calculation, traceability and sensitivity analysis</small></summary><div className="detail-content">{result.recommendations.length === 0 ? <EmptyRecommendations /> : <div className="recommendation-list">{result.recommendations.map((recommendation, index) => <RecommendationCard key={recommendation.recommendation_id} recommendation={recommendation} rank={index + 1} />)}</div>}</div></details>

        <details open><summary><span>Complete What-if Simulator</span><small>Temporary scenario values · never saved</small></summary><div className="detail-content"><WhatIfSimulator key={`${uploadId}:${result.employee_id}`} analysis={result} uploadId={uploadId} onResult={setScenarioResult} /></div></details>

        <details><summary><span>Research Provenance and Limitations</span><small>Sources, rules and validation boundaries</small></summary><div className="detail-content"><IntegrationStatus metadata={result.metadata} /><aside className="decision-notice"><div><p className="eyebrow">Research and ethics</p><h2>Decision Support Notice</h2></div><p>This system supports HR review and does not replace human judgment. Synthetic probabilities, sensitivities, recommendation rankings, and scenario differences are not validated intervention effects and must not be used as automated employment decisions.</p></aside></div></details>
      </section>
    </div>}
  </section>
}
