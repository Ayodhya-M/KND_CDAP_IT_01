import { useState } from 'react'
import type { SourceAnalysis } from './sourceDataApi'

const names: Record<string, string> = { economic: 'A — Economic baseline', additive: 'B — Additive (main comparison)', interaction: 'C — Salary interaction' }
const display = (value: number | null, suffix = '') => value === null ? 'Unavailable' : `${value.toLocaleString('en-LK', { maximumFractionDigits: 2 })}${suffix}`

export default function FinancialBurdenPanel({ value }: { value: NonNullable<SourceAnalysis['financial_burden_adjustment']> }) {
  const [enabled, setEnabled] = useState(false)
  return <section className="validation-summary">
    <h2>Experimental Financial Burden Adjustment</h2>
    <label><input type="checkbox" checked={enabled} onChange={event => setEnabled(event.target.checked)} /> Display experimental adjustment: {enabled ? 'ON' : 'OFF'}</label>
    {enabled && <>
      <p>{value.disclaimer}</p><p><strong>Assumption:</strong> {value.assumption}</p>
      <p>Scenario month: {value.survey_month}. Annual bonus is excluded. Prediction continues to use original Formula B.</p>
      <div className="summary-grid">
        <span>Original EESI (B)<strong>{display(value.original_eesi, ' / 100')}</strong></span>
        <span>Experimental adjusted EESI (B)<strong>{display(value.adjusted_eesi, ' / 100')}</strong></span>
        <span>Difference (adjusted − original)<strong>{display(value.difference, ' points')}</strong></span>
        <span>Monthly total income<strong>{display(value.total_monthly_income, ' LKR')}</strong></span>
        <span>Monthly household expenses<strong>{display(value.household_expenses, ' LKR')}</strong></span>
        <span>Monthly debt repayments<strong>{display(value.debt_repayments, ' LKR')}</strong></span>
        <span>Monthly financial commitments<strong>{display(value.financial_commitments, ' LKR')}</strong></span>
        <span>Financial burden (capped at 100%)<strong>{display(value.burden_percentage, '%')}</strong></span>
      </div>
      {!value.available && <p role="status">Adjustment unavailable: {value.reason} Missing financial values are not treated as zero.</p>}
      {value.available && <div className="mapping-table-wrap"><table><caption>Original formulas compared with separate experimental adjustments</caption><thead><tr><th>Formula</th><th>Original EESI</th><th>Experimental adjusted EESI</th><th>Difference (points)</th></tr></thead><tbody>{Object.entries(value.comparisons).map(([name, score]) => <tr key={name}><td>{names[name] ?? name}</td><td>{display(score.original)}</td><td>{display(score.adjusted)}</td><td>{display(score.difference)}</td></tr>)}</tbody></table></div>}
      <p>T = base salary + allowances; M = household expenses + debt repayments; F = min(1, M / T), for T &gt; 0.</p>
      <p>Adjusted EESI = 0.70 × original EESI + 0.30 × (100 × F). Formula D is not available for this dataset.</p>
    </>}
  </section>
}
