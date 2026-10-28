import { useEffect, useState } from 'react'
import { getMappingUploadChoices, getRetentionRecommendations, RetentionRequestError, type MappingUploadChoice, type Module4RecommendationResponse } from '../api'
import { EmployeeSearch } from '../components/EmployeeSearch'
import { EmptyRecommendations } from '../components/EmptyRecommendations'
import { IntegrationStatus } from '../components/IntegrationStatus'
import { RecommendationCard } from '../components/RecommendationCard'
import { RiskFactorsList } from '../components/RiskFactorsList'
import { RiskSummaryCard } from '../components/RiskSummaryCard'
import { WhatIfSimulator } from '../components/WhatIfSimulator'

export function Module4Dashboard() {
  const [employeeId, setEmployeeId] = useState('')
  const [result, setResult] = useState<Module4RecommendationResponse | null>(null)
  const [validationError, setValidationError] = useState('')
  const [requestError, setRequestError] = useState('')
  const [loading, setLoading] = useState(false)
  const [uploads, setUploads] = useState<MappingUploadChoice[]>([])
  const [uploadId, setUploadId] = useState('')
  const [uploadsLoading, setUploadsLoading] = useState(true)
  const [uploadsError, setUploadsError] = useState('')
  const [demo, setDemo] = useState(true)

  const loadUploads = async () => {
    setUploadsLoading(true)
    setUploadsError('')
    try {
      const response = await getMappingUploadChoices()
      setUploads(response.hr_uploads)
      setUploadId((current) => response.hr_uploads.some((upload) => upload.id === current)
        ? current
        : response.hr_uploads.find((upload) => upload.record_count === 300)?.id ?? '')
    } catch {
      setUploads([])
      setUploadId('')
      setUploadsError('HR dataset uploads could not be loaded. Confirm that the backend is available, then retry.')
    } finally {
      setUploadsLoading(false)
    }
  }

  useEffect(() => { void loadUploads() }, [])

  const analyzeEmployee = async () => {
    const normalizedId = employeeId.trim()
    setValidationError('')
    setRequestError('')
    setResult(null)
    if (!normalizedId) {
      setValidationError('Enter an employee ID before starting the analysis.')
      return
    }
    if (!uploadId) {
      setValidationError('Select an HR dataset before starting the analysis.')
      return
    }
    setLoading(true)
    try {
      setResult(await getRetentionRecommendations(normalizedId, uploadId, demo))
      setEmployeeId(normalizedId)
    } catch (error) {
      setRequestError(error instanceof RetentionRequestError
        ? error.message
        : 'An unexpected error occurred while loading the retention analysis.')
    } finally {
      setLoading(false)
    }
  }

  const selectedUpload = uploads.find((upload) => upload.id === uploadId)

  return <section className="module4-dashboard">
    <header className="module4-header page-intro">
      <div><p className="eyebrow">Module 4 · Decision intelligence</p><h1>Retention Strategies</h1><p className="muted">Personalized and transparent retention options for human-led HR decision support.</p></div>
      <span className="research-badge">Synthetic research demonstration</span>
    </header>

    <fieldset className="module4-mode-selector" disabled={loading}>
      <legend>Analysis mode</legend>
      <label className={demo ? 'active' : ''}>
        <input type="radio" name="module4-mode" checked={demo} onChange={() => { setDemo(true); setResult(null); setRequestError('') }} />
        <span><strong>Connected Synthetic Pilot</strong><small>Preferred viva mode · calculated pilot EESI + saved synthetic turnover model</small></span>
        <em>Recommended</em>
      </label>
      <label className={!demo ? 'active' : ''}>
        <input type="radio" name="module4-mode" checked={!demo} onChange={() => { setDemo(false); setResult(null); setRequestError('') }} />
        <span><strong>Configured Providers</strong><small>Development compatibility mode; current configuration may return mock fixtures</small></span>
      </label>
    </fieldset>
    {demo && <div className="synthetic-mode-notice" role="note"><strong>Research scope:</strong> Select the matching 300-person pilot upload. Probabilities come from the saved synthetic model, risk bands remain unclassified, and input sensitivities are not SHAP values or causal effects.</div>}

    <section className="analysis-toolbar" aria-labelledby="analysis-controls-heading">
      <div className="analysis-toolbar-heading"><span>01</span><div><p className="eyebrow">Employee analysis</p><h2 id="analysis-controls-heading">Select an employee record</h2></div></div>
      <div className="module4-dataset-picker" aria-labelledby="module4-dataset-heading">
        <label id="module4-dataset-heading" htmlFor="module4-upload">HR dataset</label>
        {uploadsLoading
          ? <p className="muted" role="status">Loading HR datasets…</p>
          : uploadsError
            ? <div className="dataset-load-error" role="alert"><span>{uploadsError}</span><button className="secondary-button" type="button" onClick={() => void loadUploads()}>Retry</button></div>
            : uploads.length === 0
              ? <p className="muted">No HR dataset uploads are available. Upload an HR dataset through Module 1 first.</p>
              : <>
                <select disabled={loading} id="module4-upload" title={selectedUpload?.original_filename} value={uploadId} onChange={(event) => { setUploadId(event.target.value); setResult(null); setRequestError(''); setValidationError('') }}>
                  <option value="">Select an HR dataset</option>
                  {uploads.map((upload) => <option key={upload.id} value={upload.id}>{upload.original_filename}</option>)}
                </select>
                {selectedUpload
                  ? <div className="dataset-metadata" aria-live="polite"><span><strong>{selectedUpload.record_count.toLocaleString()}</strong> records</span><span>Uploaded {new Date(selectedUpload.uploaded_at).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })}</span></div>
                  : <p className="field-help">Select the HR upload that contains the employee record.</p>}
              </>}
      </div>
      <EmployeeSearch employeeId={employeeId} loading={loading} validationError={validationError}
        onEmployeeIdChange={(value) => { setEmployeeId(value); setValidationError(''); setResult(null) }}
        onSubmit={() => void analyzeEmployee()} />
    </section>

    {loading && <div className="analysis-loading" role="status" aria-live="polite"><span className="loading-indicator" aria-hidden="true" /><div><strong>Preparing retention analysis</strong><p>Loading employee context, calculating EESI, and requesting the selected prediction provider…</p></div></div>}
    {requestError && <div className="retention-error" role="alert"><strong>Analysis could not be completed</strong><p>{requestError}</p><small>Check the selected upload, employee ID, model availability, or backend connection, then try again.</small></div>}

    {result && <div className="retention-results">
      <section className="employee-overview" aria-labelledby="employee-overview-heading">
        <div className="section-heading"><div className="numbered-heading"><span>02</span><div><p className="eyebrow">Employee risk overview</p><h2 id="employee-overview-heading">{result.employee_id}</h2></div></div><div className="provenance-pills"><span>Module 1 · Database record</span><span>Module 2 · {result.metadata.module2_source}</span><span>Module 3 · {result.metadata.module3_source}</span></div></div>
        <div className="employee-insight-grid">
          <dl className="employee-profile-grid">
            <div><dt>Department</dt><dd>{result.employee_profile.department ?? 'Not available'}</dd></div>
            <div><dt>Job role</dt><dd>{result.employee_profile.job_role ?? 'Not available'}</dd></div>
            <div><dt>Job level</dt><dd>{result.employee_profile.job_level ?? 'Not available'}</dd></div>
            <div><dt>Years at company</dt><dd>{result.employee_profile.years_at_company ?? 'Not available'}</dd></div>
            <div><dt>Overtime</dt><dd>{result.employee_profile.overtime === null ? 'Not available' : result.employee_profile.overtime ? 'Yes' : 'No'}</dd></div>
            <div><dt>Job satisfaction</dt><dd>{result.employee_profile.job_satisfaction ?? 'Not available'}</dd></div>
          </dl>
          <div className="risk-summary-grid">
            <RiskSummaryCard label="Turnover probability" value={`${(result.turnover_probability * 100).toFixed(2)}%`} level={result.risk_level} description={result.metadata.data_mode === 'synthetic_demo_integration' ? 'Saved synthetic-model estimate' : 'Current provider estimate'} />
            <RiskSummaryCard label="Calculated EESI" value={result.eesi_score.toFixed(2)} level={result.economic_pressure_level} description="Economic-pressure integration result" />
          </div>
        </div>
      </section>

      <div className="retention-workspace-grid">
        <RiskFactorsList factors={result.important_risk_factors} demo={result.metadata.data_mode === 'synthetic_demo_integration'} />
        <section className="retention-section" aria-labelledby="recommendations-heading">
          <div className="section-heading"><div className="numbered-heading"><span>03</span><div><p className="eyebrow">Personalized decision support</p><h2 id="recommendations-heading">Retention Recommendations</h2></div></div><span className="item-count">{result.recommendations.length} action{result.recommendations.length === 1 ? '' : 's'}</span></div>
          {result.recommendations.length === 0 ? <EmptyRecommendations /> : <div className="recommendation-list">{result.recommendations.map((recommendation, index) => <RecommendationCard key={recommendation.recommendation_id} recommendation={recommendation} rank={index + 1} />)}</div>}
        </section>
      </div>

      <WhatIfSimulator key={`${uploadId}:${result.employee_id}`} analysis={result} uploadId={uploadId} />
      <div className="governance-grid">
        <IntegrationStatus metadata={result.metadata} />
        <aside className="decision-notice"><div><p className="eyebrow">Research and ethics</p><h2>Decision Support Notice</h2></div><p>This system supports HR review and does not replace human judgment. Synthetic probabilities, sensitivities, recommendation rankings, and scenario differences are not validated intervention effects and must not be used as automated employment decisions.</p></aside>
      </div>
    </div>}
  </section>
}
