import { useState } from 'react'
import { getRetentionRecommendations, RetentionRequestError, type Module4RecommendationResponse } from '../api'
import { EmployeeSearch } from '../components/EmployeeSearch'
import { EmptyRecommendations } from '../components/EmptyRecommendations'
import { IntegrationStatus } from '../components/IntegrationStatus'
import { RecommendationCard } from '../components/RecommendationCard'
import { RiskFactorsList } from '../components/RiskFactorsList'
import { RiskSummaryCard } from '../components/RiskSummaryCard'

export function Module4Dashboard() {
  const [employeeId, setEmployeeId] = useState('')
  const [result, setResult] = useState<Module4RecommendationResponse | null>(null)
  const [validationError, setValidationError] = useState('')
  const [requestError, setRequestError] = useState('')
  const [loading, setLoading] = useState(false)

  const analyzeEmployee = async () => {
    const normalizedId = employeeId.trim()
    setValidationError('')
    setRequestError('')
    setResult(null)
    if (!normalizedId) {
      setValidationError('Enter an employee ID before starting the analysis.')
      return
    }

    setLoading(true)
    try {
      setResult(await getRetentionRecommendations(normalizedId))
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
    <header className="module4-header">
      <div><p className="eyebrow"></p><h1>Employee Retention Decision Support</h1><p className="muted">Personalized and explainable retention recommendations for HR decision support</p></div>
    </header>

    <EmployeeSearch
      employeeId={employeeId}
      loading={loading}
      validationError={validationError}
      onEmployeeIdChange={(value) => { setEmployeeId(value); setValidationError('') }}
      onSubmit={() => void analyzeEmployee()}
    />

    {loading && <div className="analysis-loading" role="status"><span className="loading-indicator" aria-hidden="true" /><div><strong>Preparing retention analysis</strong><p>Loading employee context and decision-support results…</p></div></div>}
    {requestError && <div className="retention-error" role="alert"><strong>Analysis could not be completed</strong><p>{requestError}</p><small>Check the employee ID or backend connection, then try again.</small></div>}

    {result && <div className="retention-results">
      <section className="employee-overview" aria-labelledby="employee-overview-heading">
        <div className="section-heading"><div><p className="eyebrow">Employee overview</p><h2 id="employee-overview-heading">{result.employee_id}</h2></div></div>
        <div className="risk-summary-grid">
          <RiskSummaryCard label="Predicted Turnover Risk" value={`${Math.round(result.turnover_probability * 100)}%`} level={result.risk_level} description="Current model-based risk estimate" />
          <RiskSummaryCard label="Economic Pressure" value={result.eesi_score.toFixed(2)} level={result.economic_pressure_level} description="Current EESI integration result" />
        </div>
      </section>

      <RiskFactorsList factors={result.important_risk_factors} />

      <section className="retention-section" aria-labelledby="recommendations-heading">
        <div className="section-heading"><div><p className="eyebrow">Decision support</p><h2 id="recommendations-heading">Recommended Retention Actions</h2></div><span className="item-count">{result.recommendations.length} action{result.recommendations.length === 1 ? '' : 's'}</span></div>
        {result.recommendations.length === 0
          ? <EmptyRecommendations />
          : <div className="recommendation-list">{result.recommendations.map((recommendation, index) => <RecommendationCard key={recommendation.recommendation_id} recommendation={recommendation} rank={index + 1} />)}</div>}
      </section>

      <IntegrationStatus metadata={result.metadata} />
    </div>}

    <aside className="decision-notice"><div><p className="eyebrow">Research and ethics</p><h2>Decision Support Notice</h2></div><p>This system provides decision support for HR professionals. Recommendations and scenario outputs should support, not replace, human judgment. No automated employment decision should be made from this output.</p></aside>
  </section>
}
