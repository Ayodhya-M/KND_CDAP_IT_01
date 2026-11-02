import { familyName } from './eesiFamilies'
import { useEffect, useState } from 'react'

const API = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'
type Formula = { id: string; name: string; expression: string; rationale: string }
type Group = { label: string; suppressed: boolean; count: number | null; scores: Record<string, { sample_mean: number; weighted_mean: number }> | null }
type RealData = {
  version: string; source_sha256: string; economic_reference_sha256: string
  source_records: number; eligible_records: number; excluded_records: number; exclusions: Record<string, number>
  formulas: Formula[]; bounds: Record<string, number[]>; reference_salary: number
  overall: Group; by_month: Group[]; by_salary_band: Group[]
  economic_months: { income_month: string; inflation: string; cpi: string; unemployment: string; unemployment_quarter: string }[]
  sources: { title: string; url: string }[]; notes: string[]
}
type Scenario = { scores: Record<string, number>; warnings: string[] }

export default function RealEesiView() {
  const [data, setData] = useState<RealData | null>(null)
  const [loadError, setLoadError] = useState('')
  const [error, setError] = useState('')
  const [measure, setMeasure] = useState<'sample_mean' | 'weighted_mean'>('sample_mean')
  const [formulaId, setFormulaId] = useState('additive')
  const [salary, setSalary] = useState(50000)
  const [month, setMonth] = useState('2024-01')
  const [result, setResult] = useState<Scenario | null>(null)
  const [busy, setBusy] = useState(false)
  useEffect(() => {
    let active = true
    fetch(`${API}/eesi/real-data`).then(async response => {
      const body = await response.json()
      if (!response.ok) throw new Error(body.detail ?? 'Unable to load real-data aggregates.')
      if (active) setData(body as RealData)
    }).catch(e => { if (active) setLoadError(e instanceof Error ? e.message : 'Unable to load real-data aggregates.') })
    return () => { active = false }
  }, [])
  const run = async () => {
    const economic = data?.economic_months.find(row => row.income_month === month)
    if (!economic) return
    setBusy(true); setError(''); setResult(null)
    try {
      const response = await fetch(`${API}/eesi/scenario`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ salary, inflation: Number(economic.inflation), cpi: Number(economic.cpi), unemployment: Number(economic.unemployment), reference_profile: 'lfs2024' }) })
      const body = await response.json()
      if (!response.ok) throw new Error(typeof body.detail === 'string' ? body.detail : 'Enter a positive monthly salary.')
      setResult(body as Scenario)
    } catch (e) { setError(e instanceof Error ? e.message : 'Scenario calculation failed.') }
    finally { setBusy(false) }
  }
  const download = () => {
    const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }))
    const anchor = document.createElement('a'); anchor.href = url; anchor.download = 'eesi-lfs2024-aggregate-evidence.json'; anchor.click(); URL.revokeObjectURL(url)
  }
  if (!data) return <section className="eesi-view"><h1>Sri Lankan employee data</h1><p className={loadError ? 'upload-error' : 'muted'} role={loadError ? 'alert' : undefined}>{loadError || 'Loading LFS 2024 aggregate results…'}</p></section>
  const formula = data.formulas.find(item => item.id === formulaId)
  const table = (groups: Group[]) => <div className="mapping-table-wrap"><table><thead><tr><th>Group / income month</th><th>Respondents</th>{data.formulas.map(item => <th key={item.id}>{familyName(item.id, item.name)}</th>)}</tr></thead><tbody>{groups.map(group => <tr key={group.label}><td>{group.label}</td><td>{group.suppressed ? 'Suppressed (<30)' : group.count}</td>{data.formulas.map(item => <td key={item.id}>{group.scores?.[item.id][measure].toFixed(2) ?? 'Suppressed'}</td>)}</tr>)}</tbody></table></div>
  return <section className="eesi-view">
    <p className="eyebrow">Real data · LFS 2024 · PP1</p><h1>Sri Lankan employee economic exposure</h1>
    <p className="muted">LFS 2024 subset ? Exploratory scores; not national stress estimates.</p>
    <div className="summary-grid"><span>Survey respondents<strong>{data.source_records.toLocaleString()}</strong></span><span>Eligible salaried employees<strong>{data.eligible_records.toLocaleString()}</strong></span><span>Outside selected cohort / invalid inputs<strong>{data.excluded_records.toLocaleString()}</strong></span></div>
    <div className="eesi-toolbar"><label className="eesi-field">Summary measure<select value={measure} onChange={e => setMeasure(e.target.value as typeof measure)}><option value="sample_mean">Sample mean (unweighted)</option><option value="weighted_mean">Descriptive weighted mean</option></select></label><button className="secondary-button" onClick={download}>Download aggregate evidence</button></div>
    <details><summary>Summary measure notes</summary><p>Weights use AnnualFactor_25Percent. Results describe the eligible subset, not national estimates.</p></details>
    <div className="eesi-formulas">{data.formulas.map(item => <button key={item.id} className={`eesi-formula ${formulaId === item.id ? 'selected' : ''}`} aria-pressed={formulaId === item.id} onClick={() => setFormulaId(item.id)}><strong>{familyName(item.id, item.name)}</strong><code>{item.expression}</code><small>Mean {data.overall.scores?.[item.id][measure].toFixed(2)} / 100</small></button>)}</div>
    <section className="validation-summary"><h2>{formula ? familyName(formula.id, formula.name) : ''}: salary groups</h2>{data.by_salary_band.map(group => <div key={group.label} className="eesi-contribution"><span>LKR {group.label}</span><progress max="100" value={group.scores?.[formulaId][measure] ?? 0} aria-label={`${group.label} average score`} /><strong>{group.scores?.[formulaId][measure].toFixed(2) ?? 'Suppressed'}</strong></div>)}{table(data.by_salary_band)}</section>
    <section className="validation-summary"><h2>Monthly formula comparison</h2>{table(data.by_month)}</section>
    <details className="validation-summary"><summary>Economic inputs and normalization</summary><div className="mapping-table-wrap"><table><thead><tr><th>Income month</th><th>NCPI (2021=100)</th><th>Inflation YoY (%)</th><th>Unemployment (%)</th><th>Unemployment period</th></tr></thead><tbody>{data.economic_months.map(row => <tr key={row.income_month}><td>{row.income_month}</td><td>{row.cpi}</td><td>{row.inflation}</td><td>{row.unemployment}</td><td>{row.unemployment_quarter}</td></tr>)}</tbody></table></div><p><strong>Frozen normalization:</strong> clip((value − lower) / (upper − lower), 0, 1).</p><p>{Object.entries(data.bounds).map(([key, bounds]) => `${key}: ${bounds.join(' to ')}`).join(' · ')}</p><p>Salary exposure V = 50,000 / (50,000 + salary). The LKR 50,000 reference remains an illustrative assumption.</p></details>
    <section className="validation-summary"><h2>Controlled scenario with official economics</h2><p className="muted">Enter a hypothetical salary and choose an income month. No individual survey record is displayed.</p><form onSubmit={e => { e.preventDefault(); void run() }}><div className="eesi-inputs"><label className="eesi-field">Monthly gross salary (LKR)<input type="number" required min="1" step="any" value={salary} onChange={e => { setSalary(Number(e.target.value)); setResult(null) }} /></label><label className="eesi-field">Income month<select value={month} onChange={e => { setMonth(e.target.value); setResult(null) }}>{data.economic_months.map(row => <option key={row.income_month}>{row.income_month}</option>)}</select></label></div><button className="primary-button" disabled={busy}>{busy ? 'Calculating…' : 'Compare formulas'}</button></form>{error && <p role="alert" className="upload-error">{error}</p>}{result && <><div className="summary-grid">{data.formulas.map(item => <span key={item.id}>{familyName(item.id, item.name)}<strong>{result.scores[item.id].toFixed(2)}</strong></span>)}</div>{result.warnings.map(item => <p key={item} className="eesi-warning">{item}</p>)}</>}</section>
    <details className="validation-summary"><summary>Sources and research notes</summary><ul>{data.notes.map(note => <li key={note}>{note}</li>)}</ul><details><summary>Exclusion audit</summary><ul>{Object.entries(data.exclusions).map(([reason, count]) => <li key={reason}>{reason.split('_').join(' ')}: {count.toLocaleString()}</li>)}</ul></details><p><strong>Calculation version:</strong> {data.version}</p><h3>Official sources</h3><ul>{data.sources.map(source => <li key={source.url}><a href={source.url} target="_blank" rel="noreferrer">{source.title}</a></li>)}</ul></details>
  </section>
}
