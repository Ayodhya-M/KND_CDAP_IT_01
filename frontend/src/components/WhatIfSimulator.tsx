import { useState } from 'react'
import { RetentionRequestError, simulateRetentionScenario, type Module4RecommendationResponse, type ScenarioValues, type WhatIfChanges, type WhatIfSimulationResponse } from '../api'

const FIELD_LABELS: Record<keyof ScenarioValues, string> = {
  salary: 'Salary',
  overtime: 'Overtime',
  job_satisfaction: 'Job satisfaction',
  work_life_balance: 'Work-life balance',
}

const displayName = (value: string) => value.replace(/_/g, ' ').replace(/\b\w/g, (letter: string) => letter.toUpperCase())

function formatValue(key: keyof ScenarioValues, value: ScenarioValues[keyof ScenarioValues]) {
  if (value === null) return 'Unavailable'
  if (key === 'overtime') return value ? 'Yes' : 'No'
  if (key === 'salary' && typeof value === 'number') return value.toLocaleString(undefined, { maximumFractionDigits: 2 })
  return String(value)
}

function changedFields(result: WhatIfSimulationResponse) {
  return (Object.keys(FIELD_LABELS) as (keyof ScenarioValues)[]).filter((key) => result.original_values[key] !== result.simulated_values[key])
}

type Props = { analysis: Module4RecommendationResponse; uploadId: string; onResult?: (result: WhatIfSimulationResponse | null) => void }

export function WhatIfSimulator({ analysis, uploadId, onResult }: Props) {
  const profile = analysis.employee_profile
  const isSynthetic = analysis.metadata.data_mode === 'synthetic_demo_integration'
  const [salary, setSalary] = useState(profile.salary?.toString() ?? '')
  const [overtime, setOvertime] = useState(profile.overtime === null ? '' : String(profile.overtime))
  const [jobSatisfaction, setJobSatisfaction] = useState(profile.job_satisfaction?.toString() ?? '')
  const [workLifeBalance, setWorkLifeBalance] = useState(profile.work_life_balance?.toString() ?? '')
  const [result, setResult] = useState<WhatIfSimulationResponse | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const clearPreviousResult = () => { setResult(null); setError(''); onResult?.(null) }
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
      setResult(null); onResult?.(null)
      return
    }
    setLoading(true); setError(''); setResult(null); onResult?.(null)
    try {
      const response = await simulateRetentionScenario(analysis.employee_id, changes, uploadId, isSynthetic)
      setResult(response); onResult?.(response)
    } catch (requestError) {
      setError(requestError instanceof RetentionRequestError ? requestError.message : 'The scenario could not be evaluated.')
    } finally { setLoading(false) }
  }

  const relativeChange = result && result.original_turnover_probability !== 0
    ? (result.simulated_turnover_probability - result.original_turnover_probability) / result.original_turnover_probability * 100
    : null
  const changes = result ? changedFields(result) : []

  return <section className="what-if-policy-simulator" aria-labelledby="what-if-heading">
    <header className="module4-section-banner what-if-banner">
      <div><p>Hypothetical model comparison</p><h2 id="what-if-heading">What-if Retention Simulator</h2></div>
      <dl><div><dt>Employee</dt><dd>{analysis.employee_id}</dd></div><div><dt>Data mode</dt><dd>{isSynthetic ? 'Connected Synthetic Pilot' : analysis.metadata.data_mode.replace(/_/g, ' ')}</dd></div></dl>
    </header>

    <div className="simulator-disclaimer"><strong>Model-based and non-causal.</strong> Scenario values are temporary, never written to Supabase, and do not prove an intervention will change turnover.</div>

    <div className="simulator-configuration">
      <div className="simulator-current-values">
        <div className="simulator-subheading"><span>Current employee context</span><small>Read-only Module 1 values</small></div>
        <dl><div><dt>Salary</dt><dd>{formatValue('salary', profile.salary)}</dd></div><div><dt>Overtime</dt><dd>{formatValue('overtime', profile.overtime)}</dd></div><div><dt>Job satisfaction</dt><dd>{formatValue('job_satisfaction', profile.job_satisfaction)}</dd></div><div><dt>Work-life balance</dt><dd>{formatValue('work_life_balance', profile.work_life_balance)}</dd></div></dl>
      </div>

      <div className="simulator-input-panel">
        <div className="simulator-subheading"><span>Configure scenario</span><small>Temporary comparison values</small></div>
        <div className="simulator-fields">
          <label>Salary<input disabled={loading} type="number" min="1" value={salary} onChange={(event) => { setSalary(event.target.value); clearPreviousResult() }} /></label>
          <label>Overtime<select disabled={loading} value={overtime} onChange={(event) => { setOvertime(event.target.value); clearPreviousResult() }}><option value="">Unavailable</option><option value="true">Yes</option><option value="false">No</option></select></label>
          <label>Job satisfaction<select disabled={loading} value={jobSatisfaction} onChange={(event) => { setJobSatisfaction(event.target.value); clearPreviousResult() }}><option value="">Unavailable</option>{[1, 2, 3, 4].map((value) => <option key={value}>{value}</option>)}</select></label>
          <label>Work-life balance <small>Recommendation rules only; not a current synthetic-model feature</small><select disabled={loading} value={workLifeBalance} onChange={(event) => { setWorkLifeBalance(event.target.value); clearPreviousResult() }}><option value="">Unavailable</option>{[1, 2, 3, 4].map((value) => <option key={value}>{value}</option>)}</select></label>
        </div>
        <div className="simulator-actions">
          {profile.salary !== null && <button className="secondary-button" type="button" disabled={loading} onClick={useSalaryIncrease}>Set salary +10%</button>}
          <button className="primary-button" type="button" disabled={loading} onClick={() => void runScenario()}>{loading ? 'Comparing scenario…' : 'Compare Scenario'}</button>
        </div>
        {error && <p className="scenario-error" role="alert">{error}</p>}
      </div>
    </div>

    {!result && !loading && <div className="simulator-empty-result"><strong>Scenario results will appear after comparison</strong><p>No simulated probability or impact is shown until the API successfully evaluates changed values.</p></div>}

    {result && <div className="simulator-output" aria-live="polite">
      <div className="before-after-flow">
        <article className="scenario-probability-card before"><span>Before</span><p>Current synthetic-model probability</p><strong>{(result.original_turnover_probability * 100).toFixed(2)}%</strong><small>{result.original_recommendations.length} recommendation{result.original_recommendations.length === 1 ? '' : 's'}</small></article>
        <div className="scenario-arrow" aria-hidden="true"><span>→</span><small>Scenario</small></div>
        <article className="scenario-probability-card after"><span>After</span><p>Simulated synthetic-model probability</p><strong>{(result.simulated_turnover_probability * 100).toFixed(2)}%</strong><small>{result.simulated_recommendations.length} recommendation{result.simulated_recommendations.length === 1 ? '' : 's'}</small></article>
        <article className="scenario-impact-card"><span>Impact</span><div><strong>{result.probability_difference > 0 ? '+' : ''}{result.probability_difference.toFixed(4)}</strong><small>percentage-point difference</small></div>{relativeChange !== null && <div><strong>{relativeChange > 0 ? '+' : ''}{relativeChange.toFixed(2)}%</strong><small>relative probability change</small></div>}</article>
      </div>

      <div className="scenario-change-summary">
        <section><h3>What changed</h3>{changes.length === 0 ? <p>No changed field was reported.</p> : <ul>{changes.map((key) => <li key={key}><strong>{FIELD_LABELS[key]}</strong><span>{formatValue(key, result.original_values[key])} → {formatValue(key, result.simulated_values[key])}</span></li>)}</ul>}</section>
        <section><h3>Recommendation comparison</h3><div className="comparison-grid"><RecommendationSummary title="Before" recommendations={result.original_recommendations} /><RecommendationSummary title="After" recommendations={result.simulated_recommendations} /></div></section>
      </div>

      {result.removed_risk_factors.length > 0 && <p className="removed-factor-note"><strong>Factors no longer applicable under prototype rules:</strong> {result.removed_risk_factors.map(displayName).join(', ')}</p>}
      <details className="simulator-limitations"><summary>Scenario assumptions and technical limitations</summary><div><p>{result.disclaimer}</p><ul>{result.assumptions.map((assumption) => <li key={assumption}>{assumption}</li>)}</ul></div></details>
    </div>}
  </section>
}

function RecommendationSummary({ title, recommendations }: { title: string; recommendations: WhatIfSimulationResponse['original_recommendations'] }) {
  return <div className="comparison-card"><h4>{title}</h4>{recommendations.length === 0 ? <p>No major actionable recommendation identified.</p> : <ol>{recommendations.map((item) => <li key={item.recommendation_id}><span>{item.title}</span><strong>{item.priority_score.toFixed(1)} · {item.priority_level}</strong></li>)}</ol>}</div>
}
