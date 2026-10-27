import { useState } from 'react'
import { RetentionRequestError, simulateRetentionScenario, type Module4RecommendationResponse, type WhatIfChanges, type WhatIfSimulationResponse } from '../api'

const displayName = (value: string) => value.replace(/_/g, ' ').replace(/\b\w/g, (letter: string) => letter.toUpperCase())

type Props = { analysis: Module4RecommendationResponse; uploadId: string }

export function WhatIfSimulator({ analysis, uploadId }: Props) {
  const profile = analysis.employee_profile
  const isSynthetic = analysis.metadata.data_mode === 'synthetic_demo_integration'
  const [salary, setSalary] = useState(profile.salary?.toString() ?? '')
  const [overtime, setOvertime] = useState(profile.overtime === null ? '' : String(profile.overtime))
  const [jobSatisfaction, setJobSatisfaction] = useState(profile.job_satisfaction?.toString() ?? '')
  const [workLifeBalance, setWorkLifeBalance] = useState(profile.work_life_balance?.toString() ?? '')
  const [result, setResult] = useState<WhatIfSimulationResponse | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const clearPreviousResult = () => { setResult(null); setError('') }
  const useSalaryIncrease = () => {
    if (profile.salary !== null) {
      setSalary((profile.salary * 1.1).toFixed(2))
      clearPreviousResult()
    }
  }

  const runScenario = async () => {
    const changes: WhatIfChanges = {}
    if (salary && Number(salary) !== profile.salary) changes.salary = Number(salary)
    if (overtime && (overtime === 'true') !== profile.overtime) changes.overtime = overtime === 'true'
    if (jobSatisfaction && Number(jobSatisfaction) !== profile.job_satisfaction) changes.job_satisfaction = Number(jobSatisfaction)
    if (workLifeBalance && Number(workLifeBalance) !== profile.work_life_balance) changes.work_life_balance = Number(workLifeBalance)
    if (Object.keys(changes).length === 0) {
      setError('Change at least one supported value before comparing the scenario.')
      setResult(null)
      return
    }
    setLoading(true); setError(''); setResult(null)
    try {
      setResult(await simulateRetentionScenario(analysis.employee_id, changes, uploadId, isSynthetic))
    } catch (requestError) {
      setError(requestError instanceof RetentionRequestError ? requestError.message : 'The scenario could not be evaluated.')
    } finally {
      setLoading(false)
    }
  }

  return <section className="retention-section what-if-section" aria-labelledby="what-if-heading">
    <div className="section-heading"><div className="numbered-heading"><span>04</span><div><p className="eyebrow">Exploratory decision support</p><h2 id="what-if-heading">Illustrative What-if Simulator</h2></div></div><span className="prototype-chip">Not a validated forecast</span></div>
    <p className="muted">{isSynthetic
      ? 'Compare temporary employee inputs using recalculated EESI and the same saved synthetic model. No employee record is changed.'
      : 'Adjust supported values to inspect prototype recommendation-rule behavior. Employee records and turnover probability remain unchanged.'}</p>
    <div className="scenario-setup">
      <div className="current-scenario">
        <div className="scenario-column-heading"><span>Current employee context</span><small>Read-only Module 1 values</small></div>
        <dl><div><dt>Salary</dt><dd>{profile.salary === null ? 'Unavailable' : profile.salary.toLocaleString()}</dd></div><div><dt>Overtime</dt><dd>{profile.overtime === null ? 'Unavailable' : profile.overtime ? 'Yes' : 'No'}</dd></div><div><dt>Job satisfaction</dt><dd>{profile.job_satisfaction ?? 'Unavailable'}</dd></div><div><dt>Work-life balance</dt><dd>{profile.work_life_balance ?? 'Unavailable'}</dd></div></dl>
      </div>
      <div className="proposed-scenario">
        <div className="scenario-column-heading"><span>Proposed scenario</span><small>Temporary values; never saved</small></div>
        <div className="scenario-form">
          <label>Salary<input disabled={loading} type="number" min="1" value={salary} onChange={(event) => { setSalary(event.target.value); clearPreviousResult() }} /></label>
          <label>Overtime<select disabled={loading} value={overtime} onChange={(event) => { setOvertime(event.target.value); clearPreviousResult() }}><option value="">Unavailable</option><option value="true">Yes</option><option value="false">No</option></select></label>
          <label>Job satisfaction<select disabled={loading} value={jobSatisfaction} onChange={(event) => { setJobSatisfaction(event.target.value); clearPreviousResult() }}><option value="">Unavailable</option>{[1, 2, 3, 4].map((value) => <option key={value}>{value}</option>)}</select></label>
          <label>Work-life balance<select disabled={loading} value={workLifeBalance} onChange={(event) => { setWorkLifeBalance(event.target.value); clearPreviousResult() }}><option value="">Unavailable</option>{[1, 2, 3, 4].map((value) => <option key={value}>{value}</option>)}</select></label>
        </div>
        <div className="scenario-actions">
          {profile.salary !== null && <button className="secondary-button" type="button" disabled={loading} onClick={useSalaryIncrease}>Set salary +10%</button>}
          <button className="primary-button" type="button" disabled={loading} onClick={() => void runScenario()}>{loading ? 'Recalculating scenario…' : 'Compare Scenario'}</button>
        </div>
        {error && <p className="scenario-error" role="alert">{error}</p>}
      </div>
    </div>
    {result && <div className="scenario-results" aria-live="polite">
      <div className="scenario-warning"><strong>{result.label}</strong><p>{result.disclaimer}</p></div>
      <div className="probability-comparison"><div><span>{isSynthetic ? 'Original synthetic-model probability' : 'Original mock risk'}</span><strong>{(result.original_turnover_probability * 100).toFixed(2)}%</strong></div><div><span>{isSynthetic ? 'Scenario synthetic-model probability' : 'Scenario mock risk'}</span><strong>{(result.simulated_turnover_probability * 100).toFixed(2)}%</strong></div><p><strong>Difference:</strong> {result.probability_difference > 0 ? '+' : ''}{result.probability_difference.toFixed(4)} percentage points {!isSynthetic && '(held constant by design)'}</p></div>
      <div className="comparison-grid">
        <RecommendationSummary title="Original recommendations" recommendations={result.original_recommendations} />
        <RecommendationSummary title="Scenario recommendations" recommendations={result.simulated_recommendations} />
      </div>
      {result.removed_risk_factors.length > 0 && <p><strong>Factors no longer applicable under prototype rules:</strong> {result.removed_risk_factors.map(displayName).join(', ')}</p>}
      <details><summary>View simulator assumptions and limitations</summary><ul>{result.assumptions.map((assumption) => <li key={assumption}>{assumption}</li>)}</ul></details>
    </div>}
  </section>
}

function RecommendationSummary({ title, recommendations }: { title: string; recommendations: WhatIfSimulationResponse['original_recommendations'] }) {
  return <div className="comparison-card"><h3>{title}</h3>{recommendations.length === 0 ? <p className="muted">No major actionable recommendation identified.</p> : <ol>{recommendations.map((item) => <li key={item.recommendation_id}><span>{item.title}</span><strong>{item.priority_score.toFixed(1)} · {item.priority_level}</strong></li>)}</ol>}</div>
}
