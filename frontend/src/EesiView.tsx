import { useEffect, useState } from 'react'
import RealEesiView from './RealEesiView'
import ImportedSourceView from './ImportedSourceView'
import HiesEesiView from './HiesEesiView'

const API = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'
type Formula = { id: string; name: string; expression: string; rationale: string }
type Result = {
  inputs: Record<string, number>; components: Record<string, number>; scores: Record<string, number>
  contributions: Record<string, Record<string, number>>; warnings: string[]; version: string
}
type Employee = Result & { employee_id: string; month: string }
type Pilot = {
  metadata: { formulas: Formula[]; normalization: string; salary_exposure: string; validation_status: string; limitations: string[]; bounds: Record<string, number[]>; reference_period: string }
  rows: Employee[]; rejected: { employee_id: string; reason: string }[]
  summary: Record<string, { mean: number; min: number; max: number }>
  months: Record<string, string>[]; data_note: string
}
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API}/eesi/${path}`, init)
  const body = await response.json()
  if (!response.ok) throw new Error(typeof body.detail === 'string' ? body.detail : 'Check the scenario values and try again.')
  return body as T
}

function SyntheticEesiView() {
  const [pilot, setPilot] = useState<Pilot | null>(null)
  const [error, setError] = useState('')
  const [selectedId, setSelectedId] = useState('')
  const [formulaId, setFormulaId] = useState('additive')
  const [query, setQuery] = useState('')
  const [scenario, setScenario] = useState({ salary: 50000, inflation: 32.6, cpi: 107.635, unemployment: 4.7, reference_salary: 50000 })
  const [result, setResult] = useState<Result | null>(null)
  const [busy, setBusy] = useState(false)
  useEffect(() => {
    let active = true
    request<Pilot>('pilot').then(data => { if (active) { setPilot(data); setSelectedId(data.rows[0]?.employee_id ?? '') } }).catch(e => { if (active) setError(e instanceof Error ? e.message : 'Unable to load pilot data.') })
    return () => { active = false }
  }, [])
  const run = async () => {
    setBusy(true); setError(''); setResult(null)
    try { setResult(await request<Result>('scenario', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(scenario) })) }
    catch (e) { setError(e instanceof Error ? e.message : 'Unable to calculate scenario.') }
    finally { setBusy(false) }
  }
  const exportResults = () => {
    if (!pilot) return
    const blob = new Blob([JSON.stringify(pilot, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a'); anchor.href = url; anchor.download = 'eesi-pp1-pilot-evidence.json'; anchor.click(); URL.revokeObjectURL(url)
  }
  const selected = pilot?.rows.find(row => row.employee_id === selectedId)
  const formula = pilot?.metadata.formulas.find(item => item.id === formulaId)
  return <section className="eesi-view">
    <p className="eyebrow">Your module · PP1 proof of concept</p><h1>Employee Economic Stress Index</h1>
    <p className="muted">Compare economic pressure and salary exposure before selecting a final EESI formula.</p>
    <div className="eesi-notice"><strong>Exploratory research prototype</strong><p>Scores are relative to the January–June 2023 pilot reference. They are not probabilities, measured financial stress, or turnover predictions. No candidate has established empirical accuracy.</p></div>
    {error && <p role="alert" className="upload-error">{error} Confirm the backend is running on the configured API address.</p>}
    {!pilot ? <p className="muted">{error ? 'Pilot data could not be loaded.' : 'Loading independent EESI pilot…'}</p> : <>
      <div className="eesi-toolbar"><p>{pilot.rows.length} employees scored · {pilot.months.length} economic months · {pilot.rejected.length} rejected</p><button className="secondary-button" onClick={exportResults}>Download calculation evidence</button></div>
      <p className="muted">{pilot.data_note} No Module 1 upload or database connection is required.</p>
      <div className="eesi-formulas">{pilot.metadata.formulas.map(item => <button key={item.id} className={`eesi-formula ${formulaId === item.id ? 'selected' : ''}`} aria-pressed={formulaId === item.id} onClick={() => setFormulaId(item.id)}><strong>{item.name}</strong><code>{item.expression}</code><small>Mean {pilot.summary[item.id]?.mean.toFixed(2)} / 100</small></button>)}</div>
      <section className="validation-summary"><h2>{formula?.name}</h2><p>{formula?.rationale}</p><p><strong>Normalization:</strong> {pilot.metadata.normalization}</p><p><strong>Salary exposure:</strong> {pilot.metadata.salary_exposure}. LKR 50,000 is an illustrative configurable reference, not an official living wage.</p><p><strong>Frozen pilot bounds:</strong> {Object.entries(pilot.metadata.bounds).map(([key, bounds]) => `${key}: ${bounds.join('–')}`).join(' · ')}</p></section>
      <section className="validation-summary"><h2>Employee score breakdown</h2><label className="eesi-field">Employee<select value={selectedId} onChange={e => setSelectedId(e.target.value)}>{pilot.rows.map(row => <option key={row.employee_id} value={row.employee_id}>{row.employee_id} · {row.month} · LKR {row.inputs.salary.toLocaleString()}</option>)}</select></label>
        {selected && <><p className="eesi-score">{selected.scores[formulaId].toFixed(2)} <small>/ 100</small></p><p className="muted">Normalized salary exposure: {selected.components.salary_exposure.toFixed(3)}</p>{Object.entries(selected.contributions[formulaId]).map(([key, value]) => <div className="eesi-contribution" key={key}><span>{key.split('_').join(' ')}</span><progress max="100" value={value} aria-label={`${key} contribution`} /><strong>{value.toFixed(2)} points</strong></div>)}<p className="muted">Contributions sum to the score. The interaction candidate applies salary exposure to each economic component.</p></>}
      </section>
      <section className="validation-summary"><h2>What happens when salary or the economy changes?</h2><p className="muted">Change one value at a time. Reference ranges remain fixed. Results appear after calculation.</p>
        <form onSubmit={e => { e.preventDefault(); void run() }}><div className="eesi-inputs">{Object.entries(scenario).map(([key, value]) => <label className="eesi-field" key={key}>{key.split('_').join(' ')}{key.includes('salary') ? ' (LKR / month)' : key === 'inflation' || key === 'unemployment' ? ' (%)' : ''}<input required type="number" step="any" min={key === 'inflation' ? undefined : key === 'unemployment' ? 0 : 0.000001} max={key === 'unemployment' ? 100 : undefined} value={value} onChange={e => { setScenario(current => ({ ...current, [key]: Number(e.target.value) })); setResult(null) }} /></label>)}</div><button className="primary-button" disabled={busy}>{busy ? 'Calculating…' : 'Compare scenario formulas'}</button></form>
        {result && <><div className="summary-grid">{pilot.metadata.formulas.map(item => <span key={item.id}>{item.name}<strong>{result.scores[item.id].toFixed(2)} / 100</strong></span>)}</div>{result.warnings.map(warning => <p className="eesi-warning" key={warning}>{warning}</p>)}</>}
      </section>
      <section className="validation-summary"><h2>Pilot comparison</h2><label className="eesi-field">Find employee<input value={query} onChange={e => setQuery(e.target.value)} placeholder="Employee ID" /></label><div className="mapping-table-wrap"><table><thead><tr><th>Employee</th><th>Month</th><th>Salary (LKR)</th>{pilot.metadata.formulas.map(item => <th key={item.id}>{item.name}</th>)}</tr></thead><tbody>{pilot.rows.filter(row => row.employee_id.toLowerCase().includes(query.toLowerCase())).map(row => <tr key={row.employee_id}><td>{row.employee_id}</td><td>{row.month}</td><td>{row.inputs.salary.toLocaleString()}</td>{pilot.metadata.formulas.map(item => <td key={item.id}>{row.scores[item.id].toFixed(2)}</td>)}</tr>)}</tbody></table></div></section>
      <section className="validation-summary"><h2>Evidence and remaining research</h2><p>Implemented: deterministic score generation, transparent contributions, three formula candidates, scenario comparison, and automated correctness checks.</p><ul>{pilot.metadata.limitations.map(item => <li key={item}>{item}</li>)}</ul><p>Next: independent survey validation, indicator ablation, weight sensitivity, held-out evaluation, and final formula selection.</p><p><a href="https://www.oecd.org/en/publications/handbook-on-constructing-composite-indicators-methodology-and-user-guide_9789264043466-en.html" target="_blank" rel="noreferrer">Composite indicator methodology (OECD/JRC)</a> · <a href="https://www.consumerfinance.gov/data-research/research-reports/financial-well-being-scale/" target="_blank" rel="noreferrer">Potential validation instrument (CFPB)</a></p></section>
    </>}
  </section>
}

export default function EesiView() {
  const [source, setSource] = useState<'additional' | 'hies' | 'real' | 'synthetic'>('hies')
  return <><div className="cleaning-buttons eesi-source-switch"><button className={source === 'additional' ? 'primary-button' : 'secondary-button'} aria-pressed={source === 'additional'} onClick={() => setSource('additional')}>Additional imported sources</button><button className={source === 'hies' ? 'primary-button' : 'secondary-button'} aria-pressed={source === 'hies'} onClick={() => setSource('hies')}>HIES 2019 · 100-person sample</button><button className={source === 'real' ? 'primary-button' : 'secondary-button'} aria-pressed={source === 'real'} onClick={() => setSource('real')}>LFS 2024 data</button><button className={source === 'synthetic' ? 'primary-button' : 'secondary-button'} aria-pressed={source === 'synthetic'} onClick={() => setSource('synthetic')}>Synthetic pilot / worked examples</button></div>{source === 'additional' ? <ImportedSourceView stage="eesi" /> : source === 'hies' ? <HiesEesiView /> : source === 'real' ? <RealEesiView /> : <SyntheticEesiView />}</>
}
