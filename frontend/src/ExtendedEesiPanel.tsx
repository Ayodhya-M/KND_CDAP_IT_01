import { useState } from 'react'
import { EXTENSION_VERSION } from './eesiFamilies'
import { analyseSource, type SourceAnalysis } from './sourceDataApi'

const number = (value: number | null | undefined) => value == null ? 'Unavailable' : value.toLocaleString('en-LK', { maximumFractionDigits: 2 })

export default function ExtendedEesiPanel({ result }: { result: SourceAnalysis }) {
  const [family, setFamily] = useState<'A' | 'B' | 'C'>('B')
  const [compared, setCompared] = useState(false)
  const [variant, setVariant] = useState<'basic' | 'extended'>('basic')
  const [salary, setSalary] = useState(String(result.inputs.Monthly_Base_Salary_LKR))
  const [scenario, setScenario] = useState<SourceAnalysis | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  async function calculateScenario() {
    const amount = Number(salary)
    if (!salary.trim() || !Number.isFinite(amount) || amount <= 0) { setError('Enter a positive monthly salary.'); return }
    setBusy(true); setError(''); setScenario(null)
    try { setScenario(await analyseSource(result.dataset.id, result.record_id, amount)) }
    catch (caught) { setError(caught instanceof Error ? caught.message : 'Scenario calculation failed.') }
    finally { setBusy(false) }
  }
  const extension = result.experimental_eesi
  const financial = result.financial_burden_adjustment
  const original = result.eesi
  if (!extension || !financial || !original) return null
  const formulas = [
    ['A - Economic Baseline', original.scores.economic, '100 × (I+C+U)/3', original.contributions.economic],
    ['B - Basic', original.scores.additive, '100 × (I+C+U+V)/4', original.contributions.additive],
    ['B - Extended (experimental; B2)', extension.scores.B2, '100 × (I+C+U+V+F)/5', extension.contributions.B2],
    ['C - Basic', original.scores.interaction, '100 × ((I+C+U)/3) × V', original.contributions.interaction],
    ['C - Extended (experimental; C2)', extension.scores.C2, '100 × ((I+C+U)/3) × ((V+F)/2)', extension.contributions.C2],
  ] as const
  const families = [
    { id: 'A', title: 'A - Economic Baseline', purpose: 'Economic pressure only.', rows: [formulas[0]] },
    { id: 'B', title: 'B - Additive Financial Exposure', purpose: 'Add salary exposure, with an optional financial burden component.', rows: [formulas[1], formulas[2]] },
    { id: 'C', title: 'C - Financial Interaction', purpose: 'Adjust economic pressure by financial exposure.', rows: [formulas[3], formulas[4]] },
  ] as const
  const selected = families.find(item => item.id === family)!
  const selectedFormula = selected.rows[family !== 'A' && variant === 'extended' ? 1 : 0]!
  return <>
    <h2>EESI formulas</h2>
    
    <div className="eesi-formulas">{families.map(item => <button type="button" key={item.id} className={`eesi-formula ${family === item.id ? 'selected' : ''}`} aria-pressed={family === item.id} onClick={() => { setFamily(item.id); setCompared(false); setVariant('basic') }}><strong>{item.title}</strong>{item.rows.map(([name, , equation]) => <div key={name}><small>{name.includes('Extended') ? 'Extended - Experimental' : item.id === 'A' ? 'Economic baseline' : 'Basic'}</small><code>{equation}</code></div>)}</button>)}</div>
    
    <section className="validation-summary"><h2>Employee score breakdown</h2><p>{result.record_id} ? {financial.survey_month} ? Salary LKR {number(original.inputs.salary)}</p>
    {family !== 'A' && <label className="eesi-field">Formula version<select value={variant} onChange={event => setVariant(event.target.value as 'basic' | 'extended')}><option value="basic">Basic</option><option value="extended">Extended (experimental)</option></select></label>}
    <p className="eesi-score">{number(selectedFormula[1])} <small>/ 100</small></p>
    {selectedFormula[3] && Object.entries(selectedFormula[3]).map(([key, value]) => <div className="eesi-contribution" key={key}><span>{key.split('_').join(' ')}</span><progress max="100" value={value} aria-label={`${key} contribution`} /><strong>{number(value)} points</strong></div>)}
    </section>
    {!extension.available && <p role="status">Extended scores unavailable: {extension.reason}</p>}
    <button type="button" className="primary-button" onClick={() => setCompared(value => !value)}>{compared ? 'Hide comparison' : 'Compare all formulas'}</button>
    {compared && <div className="mapping-table-wrap"><table><caption>Results for {result.record_id}</caption><thead><tr><th>Family</th><th>Basic / 100</th><th>Extended / 100 (experimental)</th><th>Difference (points)</th></tr></thead><tbody><tr><td>A - Economic Baseline</td><td>{number(original.scores.economic)}</td><td>Not applicable</td><td>Not applicable</td></tr><tr><td>B - Additive</td><td>{number(original.scores.additive)}</td><td>{number(extension.scores.B2)}</td><td>{number(extension.differences.B2_minus_B)}</td></tr><tr><td>C - Interaction</td><td>{number(original.scores.interaction)}</td><td>{number(extension.scores.C2)}</td><td>{number(extension.differences.C2_minus_C)}</td></tr></tbody></table></div>}
    <p className="muted">Extended scores are experimental. Predictions use Basic B.</p>
    <section className="validation-summary"><h2>What happens when salary changes?</h2><p className="muted">Other inputs stay fixed. Saved records stay unchanged.</p>
    <form onSubmit={event => { event.preventDefault(); void calculateScenario() }}><label className="eesi-field">Monthly base salary (LKR)<input required type="number" min="0.000001" step="any" disabled={busy} value={salary} onChange={event => { setSalary(event.target.value); setScenario(null) }} /></label><button className="primary-button" disabled={busy}>{busy ? 'Calculating...' : 'Compare scenario formulas'}</button></form>
    {error && <p role="alert" className="upload-error">{error}</p>}
    {scenario && <><div className="summary-grid">{[
      ['A - Economic Baseline', original.scores.economic, scenario.eesi?.scores.economic],
      ['B - Basic', original.scores.additive, scenario.eesi?.scores.additive],
      ['B - Extended (experimental)', extension.scores.B2, scenario.experimental_eesi?.scores.B2],
      ['C - Basic', original.scores.interaction, scenario.eesi?.scores.interaction],
      ['C - Extended (experimental)', extension.scores.C2, scenario.experimental_eesi?.scores.C2],
    ].map(([name, before, after]) => <span key={name as string}>{name}<strong>{number(after as number | undefined)} / 100</strong><small>Original: {number(before as number | undefined)} ? Change: {typeof after === 'number' && typeof before === 'number' ? number(after - before) : 'Unavailable'} points</small></span>)}</div>
    <p>Raw financial burden: {number(scenario.financial_burden_adjustment?.burden_raw)}; capped: {number(scenario.financial_burden_adjustment?.burden_capped)}.</p>
    {scenario.eesi?.warnings.map(warning => <p className="eesi-warning" key={warning}>{warning}</p>)}</>}
    </section>
    <details><summary>Inputs, calculation details and research notes</summary>
    <p>Basic version: {original.version}. Extended version: {EXTENSION_VERSION}.</p>
    <h3>Financial inputs and ratios</h3>
    <p>{financial.assumption} Annual bonuses are excluded. Scenario month: {financial.survey_month}.</p>
    <div className="mapping-table-wrap"><table><thead><tr><th>Input / variable</th><th>Value</th></tr></thead><tbody>
      {['Monthly_Base_Salary_LKR', 'Monthly_Allowances_LKR', 'Monthly_Household_Expenses_LKR', 'Monthly_Debt_Payments_LKR'].map(key => <tr key={key}><td>{key}</td><td>{number(typeof result.inputs[key] === 'number' ? result.inputs[key] : null)} LKR</td></tr>)}
      {Object.entries({ 'T: salary + allowances (LKR)': financial.total_monthly_income, 'M: expenses + debt (LKR)': financial.financial_commitments, 'F_raw = M/T (uncapped ratio)': financial.burden_raw, 'F = min(1, F_raw)': financial.burden_capped, 'DSR = debt/T (uncapped ratio)': financial.debt_service_ratio }).map(([key, value]) => <tr key={key}><td>{key}</td><td>{number(value)}</td></tr>)}
    </tbody></table></div>
    <p>Raw burden: {financial.burden_raw == null ? 'Unavailable' : `${number(financial.burden_raw * 100)}%`}; capped burden: {number(financial.burden_percentage)}%.</p>
    <h3>Economic inputs and normalized components</h3>
    <p>Historical normalization and salary exposure are reused unchanged; I, C, U, V and F range from 0 to 1.</p>
    <div className="mapping-table-wrap"><table><thead><tr><th>Indicator</th><th>Raw input</th><th>Normalized component</th></tr></thead><tbody>
      {([['Inflation (%)', 'inflation'], ['CPI (NCPI 2013=100)', 'cpi'], ['Unemployment (%)', 'unemployment']] as const).map(([label, key]) => <tr key={key}><td>{label}</td><td>{number(original.inputs[key])}</td><td>{number(original.components[key])}</td></tr>)}
      <tr><td>V = R/(R+S)</td><td>R: {number(original.inputs.reference_salary)}; S: {number(original.inputs.salary)} LKR</td><td>{number(original.components.salary_exposure)}</td></tr>
    </tbody></table></div>
    {original.warnings.map(warning => <p key={warning}>{warning}</p>)}
    <h3>Formula breakdowns</h3>
    {formulas.map(([name, , equation, contributions]) => <details key={name}><summary>{name}: {equation}</summary><p>{contributions ? Object.entries(contributions).map(([key, value]) => `${key}: ${number(value)} points`).join('; ') : 'Unavailable'}</p></details>)}
    <p>For C2, each economic contribution is multiplied by (V+F)/2; contributions sum to C2.</p>
    <h3>Research scope and limitations</h3>
    <p>B2/C2 are proposed, unvalidated equations using synthetic data. Equal weights are unvalidated. CPI and inflation overlap; salary enters both V and F. Household expenses are compared with individual income. Capping hides differences above 100% (29/50 records in the inspected import). Synthetic data cannot validate actual stress.</p>
    <p>Conceptual foundations: <a href="https://www.consumerfinance.gov/data-research/research-reports/financial-well-being-scale/">CFPB financial well-being</a>, <a href="https://www.cgap.org/research/publication/measuring-financial-health-framework">CGAP financial health</a>, <a href="https://www.oecd.org/en/publications/g20-policy-note-on-financial-well-being_7332c99d-en.html">OECD financial well-being</a>, and <a href="https://www.oecd.org/en/publications/handbook-on-constructing-composite-indicators-methodology-and-user-guide_9789264043466-en.html">OECD/JRC composite-index methodology</a>. These sources motivate the concepts and evaluation approach; they do not supply or validate B2/C2.</p>
    </details>
  </>
}
