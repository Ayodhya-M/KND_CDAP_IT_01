import type { Module4RiskFactor } from '../api'

const displayNames: Record<string, string> = {
  overtime: 'Overtime',
  job_satisfaction: 'Job Satisfaction',
  work_life_balance: 'Work-Life Balance',
  environment_satisfaction: 'Environment Satisfaction',
  business_travel: 'Business Travel',
  distance_from_home: 'Distance From Home',
  salary: 'Salary',
}

export function formatFeatureName(featureName: string) {
  return displayNames[featureName] ?? featureName
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')
}

function formatFeatureValue(value: unknown) {
  if (value === null || value === undefined || value === '') return 'Not supplied'
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

export function RiskFactorsList({ factors }: { factors: Module4RiskFactor[] }) {
  return <section className="retention-section" aria-labelledby="risk-factors-heading">
    <div className="section-heading">
      <div><p className="eyebrow">Prediction explanation</p><h2 id="risk-factors-heading">Important Risk Factors</h2></div>
      <span className="item-count">{factors.length} factor{factors.length === 1 ? '' : 's'}</span>
    </div>
    {factors.length === 0
      ? <p className="section-empty">No major risk factor was supplied in the current prediction explanation.</p>
      : <div className="risk-factor-list">{factors.map((factor, index) => <article className="risk-factor-row" key={`${factor.feature_name}-${index}`}>
        <span className="factor-rank" aria-hidden="true">{index + 1}</span>
        <div><strong>{formatFeatureName(factor.feature_name)}</strong><small>Current value: {formatFeatureValue(factor.feature_value)}</small></div>
        <div className="factor-contribution"><span>Model Contribution</span><strong>{factor.contribution.toFixed(2)}</strong></div>
      </article>)}</div>}
  </section>
}
