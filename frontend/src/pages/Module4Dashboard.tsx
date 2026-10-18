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

  const loadUploads = async () => {
    setUploadsLoading(true)
    setUploadsError('')
    try {
      const response = await getMappingUploadChoices()
      setUploads(response.hr_uploads)
      setUploadId((current) => response.hr_uploads.some((upload) => upload.id === current) ? current : '')
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
      setResult(await getRetentionRecommendations(normalizedId, uploadId))
      setEmployeeId(normalizedId)
    } catch (error) {
      setRequestError(error instanceof RetentionRequestError
        ? error.message
        : 'An unexpected error occurred while loading the retention analysis.')
    } finally {
      setLoading(false)
    }
  }

  return <section className="module4-dashboard">
    <header className="module4-header page-intro">
      <div><p className="eyebrow">Module 4 · Decision intelligence</p><h1>Retention Strategies</h1><p className="muted">Personalized, explainable retention actions that support informed HR review.</p></div>
    </header>

    <div className="analysis-controls">
    <section className="module4-dataset-picker" aria-labelledby="module4-dataset-heading">
      <label id="module4-dataset-heading" htmlFor="module4-upload">HR dataset</label>
      {uploadsLoading ? <p className="muted" role="status">Loading HR datasets…</p> : uploadsError ? <div className="dataset-load-error" role="alert"><span>{uploadsError}</span><button className="secondary-button" type="button" onClick={() => void loadUploads()}>Retry</button></div> : uploads.length === 0 ? <p className="muted">No HR dataset uploads are available. Upload an HR dataset through Module 1 first.</p> : <><select id="module4-upload" value={uploadId} onChange={(event) => { setUploadId(event.target.value); setResult(null); setRequestError(''); setValidationError('') }}><option value="">Select an HR dataset</option>{uploads.map((upload) => <option key={upload.id} value={upload.id}>{upload.original_filename} — {upload.record_count} records — {new Date(upload.uploaded_at).toLocaleString()}</option>)}</select><p className="field-help">The selected upload scopes employee lookup and prevents ambiguity across repeated employee IDs.</p></>}
    </section>

    <EmployeeSearch
      employeeId={employeeId}
      loading={loading}
      validationError={validationError}
      onEmployeeIdChange={(value) => { setEmployeeId(value); setValidationError('') }}
      onSubmit={() => void analyzeEmployee()}
    />
    </div>

    {loading && <div className="analysis-loading" role="status"><span className="loading-indicator" aria-hidden="true" /><div><strong>Preparing retention analysis</strong><p>Loading employee context and decision-support results…</p></div></div>}
    {requestError && <div className="retention-error" role="alert"><strong>Analysis could not be completed</strong><p>{requestError}</p><small>Check the employee ID or backend connection, then try again.</small></div>}

    {result && <div className="retention-results">
      <section className="employee-overview" aria-labelledby="employee-overview-heading">
        <div className="section-heading"><div><p className="eyebrow">Employee overview</p><h2 id="employee-overview-heading">{result.employee_id}</h2></div></div>
        <div className="risk-summary-grid">
          <RiskSummaryCard label="Predicted Turnover Risk" value={`${Math.round(result.turnover_probability * 100)}%`} level={result.risk_level} description="Current model-based risk estimate" />
          <RiskSummaryCard label="Economic Pressure" value={result.eesi_score.toFixed(2)} level={result.economic_pressure_level} description="Current EESI integration result" />
        </div>
        <dl className="employee-profile-grid">
          <div><dt>Department</dt><dd>{result.employee_profile.department ?? 'Not available'}</dd></div>
          <div><dt>Job role</dt><dd>{result.employee_profile.job_role ?? 'Not available'}</dd></div>
          <div><dt>Job level</dt><dd>{result.employee_profile.job_level ?? 'Not available'}</dd></div>
          <div><dt>Years at company</dt><dd>{result.employee_profile.years_at_company ?? 'Not available'}</dd></div>
          <div><dt>Overtime</dt><dd>{result.employee_profile.overtime === null ? 'Not available' : result.employee_profile.overtime ? 'Yes' : 'No'}</dd></div>
          <div><dt>Job satisfaction</dt><dd>{result.employee_profile.job_satisfaction ?? 'Not available'}</dd></div>
        </dl>
      </section>

      <div className="retention-workspace-grid">
      <RiskFactorsList factors={result.important_risk_factors} />
      <section className="retention-section" aria-labelledby="recommendations-heading">
        <div className="section-heading"><div><p className="eyebrow">Decision support</p><h2 id="recommendations-heading">Recommended Retention Actions</h2></div><span className="item-count">{result.recommendations.length} action{result.recommendations.length === 1 ? '' : 's'}</span></div>
        {result.recommendations.length === 0
          ? <EmptyRecommendations />
          : <div className="recommendation-list">{result.recommendations.map((recommendation, index) => <RecommendationCard key={recommendation.recommendation_id} recommendation={recommendation} rank={index + 1} />)}</div>}
      </section>
      </div>

      <WhatIfSimulator key={`${uploadId}:${result.employee_id}`} analysis={result} uploadId={uploadId} />

      <IntegrationStatus metadata={result.metadata} />
    </div>}

    <aside className="decision-notice"><div><p className="eyebrow">Research and ethics</p><h2>Decision Support Notice</h2></div><p>This system provides decision support for HR professionals. Recommendations and scenario outputs should support, not replace, human judgment. No automated employment decision should be made from this output.</p></aside>
  </section>
}
