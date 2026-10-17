import { useState } from 'react'
import {
  RetentionRequestError,
  simulateRetentionScenario,
  type Module4RecommendationResponse,
  type WhatIfChanges,
  type WhatIfSimulationResponse,
} from '../api'

const displayName = (value: string) => value.replace(/_/g, ' ').replace(/\b\w/g, (letter: string) => letter.toUpperCase())

type Props = {
  analysis: Module4RecommendationResponse
}

export function WhatIfSimulator({ analysis }: Props) {
  const profile = analysis.employee_profile
  const [salary, setSalary] = useState(profile.salary?.toString() ?? '')
  const [overtime, setOvertime] = useState(profile.overtime === null ? '' : String(profile.overtime))
  const [jobSatisfaction, setJobSatisfaction] = useState(profile.job_satisfaction?.toString() ?? '')
  const [workLifeBalance, setWorkLifeBalance] = useState(profile.work_life_balance?.toString() ?? '')
  const [result, setResult] = useState<WhatIfSimulationResponse | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

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
      setResult(await simulateRetentionScenario(analysis.employee_id, changes))
    } catch (requestError) {
      setError(requestError instanceof RetentionRequestError ? requestError.message : 'The scenario could not be evaluated.')
    } finally {
      setLoading(false)
    }
  }

  return <section className="retention-section what-if-section" aria-labelledby="what-if-heading">
    <div className="section-heading"><div><p className="eyebrow">Exploratory decision support</p><h2 id="what-if-heading">Illustrative What-if Simulator</h2></div><span className="prototype-chip">Not a validated forecast</span></div>
    <p className="muted">Adjust supported values to see how the prototype recommendation rules respond. Employee records and turnover probability are not changed.</p>
    <div className="scenario-form">
      <label>Salary<input type="number" min="1" value={salary} onChange={(event) => setSalary(event.target.value)} /></label>
      <label>Overtime<select value={overtime} onChange={(event) => setOvertime(event.target.value)}><option value="">Unavailable</option><option value="true">Yes</option><option value="false">No</option></select></label>
      <label>Job satisfaction<select value={jobSatisfaction} onChange={(event) => setJobSatisfaction(event.target.value)}><option value="">Unavailable</option>{[1, 2, 3, 4].map((value) => <option key={value}>{value}</option>)}</select></label>
      <label>Work-life balance<select value={workLifeBalance} onChange={(event) => setWorkLifeBalance(event.target.value)}><option value="">Unavailable</option>{[1, 2, 3, 4].map((value) => <option key={value}>{value}</option>)}</select></label>
    </div>
    <button className="primary-button" type="button" disabled={loading} onClick={() => void runScenario()}>{loading ? 'Comparing…' : 'Compare Scenario'}</button>
    {error && <p className="scenario-error" role="alert">{error}</p>}
    {result && <div className="scenario-results">
      <div className="scenario-warning"><strong>{result.label}</strong><p>{result.disclaimer}</p></div>
      <div className="probability-comparison"><div><span>Current mock risk</span><strong>{Math.round(result.original_turnover_probability * 100)}%</strong></div><div><span>Scenario mock risk</span><strong>{Math.round(result.simulated_turnover_probability * 100)}%</strong></div><p>Difference: {result.probability_difference.toFixed(0)} percentage points (held constant by design)</p></div>
      <div className="comparison-grid">
        <RecommendationSummary title="Before" recommendations={result.original_recommendations} />
        <RecommendationSummary title="After illustrative rule check" recommendations={result.simulated_recommendations} />
      </div>
      {result.removed_risk_factors.length > 0 && <p><strong>Factors no longer applicable under prototype rules:</strong> {result.removed_risk_factors.map(displayName).join(', ')}</p>}
      <details><summary>View simulator assumptions</summary><ul>{result.assumptions.map((assumption) => <li key={assumption}>{assumption}</li>)}</ul></details>
    </div>}
  </section>
}

function RecommendationSummary({ title, recommendations }: { title: string, recommendations: WhatIfSimulationResponse['original_recommendations'] }) {
  return <div className="comparison-card"><h3>{title}</h3>{recommendations.length === 0 ? <p className="muted">No major actionable recommendation identified.</p> : <ol>{recommendations.map((item) => <li key={item.recommendation_id}><span>{item.title}</span><strong>{item.priority_score.toFixed(0)} · {item.priority_level}</strong></li>)}</ol>}</div>
}
