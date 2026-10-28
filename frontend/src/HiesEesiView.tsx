import { useEffect, useRef, useState } from 'react'
import FormulaDPanel from './FormulaDPanel'
import { calculateHiesScenario, getHiesDataset, type HiesCalculation, type HiesDataset, type HiesScenario } from './api'

const labels: Record<keyof HiesScenario, string> = { salary: 'Wages (LKR / month)', inflation: 'Inflation, year on year (%)', cpi: 'NCPI (2013 = 100)', unemployment: 'Unemployment (%)', reference_salary: 'Illustrative reference salary (LKR)' }
const amount = (value: number | null) => value === null ? 'Not reported' : value.toLocaleString('en-LK', { maximumFractionDigits: 2 })

export default function HiesEesiView() {
  const [data, setData] = useState<HiesDataset | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [selectedId, setSelectedId] = useState('')
  const [formulaId, setFormulaId] = useState('additive')
  const [query, setQuery] = useState('')
  const [scenario, setScenario] = useState<HiesScenario | null>(null)
  const [result, setResult] = useState<HiesCalculation | null>(null)
  const [scenarioBusy, setScenarioBusy] = useState(false)
  const [scenarioError, setScenarioError] = useState('')
  const scenarioRequest = useRef(0)
  const [formulaDEvidence, setFormulaDEvidence] = useState<unknown>(null)
  const selected = data?.records.find(row => row.sample_id === selectedId)
  const formula = data?.metadata.formulas.find(item => item.id === formulaId)
  const load = async (importPrepared = false) => {
    setBusy(true); setError('')
    try {
      const next = await getHiesDataset(importPrepared)
      setData(next)
      setSelectedId(current => next.records.some(row => row.sample_id === current) ? current : next.records[0]?.sample_id ?? '')
    } catch (caught) { setError(caught instanceof Error ? caught.message : 'Unable to load HIES data.') }
    finally { setBusy(false) }
  }
  useEffect(() => { void load() }, [])
  useEffect(() => {
    scenarioRequest.current += 1
    setScenarioBusy(false)
    setScenario(selected && data ? { salary: selected.salary, inflation: selected.inflation, cpi: selected.cpi, unemployment: selected.unemployment, reference_salary: data.metadata.reference_salary } : null)
    setResult(null); setScenarioError('')
  }, [selected, data])
  const runScenario = async () => {
    if (!scenario) return
    const requestId = ++scenarioRequest.current
    setScenarioBusy(true); setScenarioError(''); setResult(null)
    try {
      const calculated = await calculateHiesScenario(scenario)
      if (requestId === scenarioRequest.current) setResult(calculated)
    }
    catch (caught) { if (requestId === scenarioRequest.current) setScenarioError(caught instanceof Error ? caught.message : 'Unable to calculate scenario.') }
    finally { if (requestId === scenarioRequest.current) setScenarioBusy(false) }
  }
  const exportEvidence = () => {
    if (!data) return
    const url = URL.createObjectURL(new Blob([JSON.stringify({ dataset: data, selected_formula: formulaId, selected_employee: selectedId, scenario, scenario_result: result, formula_d: formulaDEvidence }, null, 2)], { type: 'application/json' }))
    const link = document.createElement('a'); link.href = url; link.download = 'hies2019-eesi-evidence.json'; link.click(); URL.revokeObjectURL(url)
  }
  return <section className="eesi-view">
    <p className="eyebrow">Module 2 · HIES 2019 · Progress presentation</p><h1>Employee Economic Stress Index</h1>
    <p className="muted">Explore 100 wage earners, their economic context and financial inputs.</p>
    {error && <p className="upload-error" role="alert">{error}</p>}
    <div className="eesi-toolbar"><div className="cleaning-buttons"><button className="secondary-button" disabled={busy} onClick={() => void load()}>Refresh records</button><button className="secondary-button" disabled={busy || !data?.prepared_available} onClick={() => void load(true)}>{busy ? 'Loading…' : data?.record_count ? 'Reimport prepared sample' : 'Import prepared sample'}</button></div><button className="primary-button" disabled={!data?.record_count} onClick={exportEvidence}>Download calculation evidence</button></div>
    {!data && !error && <p role="status">Loading HIES workspace…</p>}
    {data && <>
      <div className="summary-grid"><span>Wage earners<strong>{data.record_count}</strong></span><span>Complete income components<strong>{data.complete_income_count}</strong></span><span>Reported household debt payments<strong>{data.debt_payment_count}</strong></span></div>
      <div className="eesi-notice"><strong>Exploratory candidate indices</strong><p>{data.note} These are not turnover probabilities or validated stress measurements.</p></div>
      {!data.record_count && <p>Import the prepared sample to begin.</p>}
      {!!data.record_count && <>
        <div className="eesi-formulas eesi-formulas-four">{data.metadata.formulas.map(item => <button key={item.id} className={`eesi-formula ${formulaId === item.id ? 'selected' : ''}`} aria-pressed={formulaId === item.id} onClick={() => setFormulaId(item.id)}><strong>{item.name}</strong><code>{item.expression}</code><small>Sample mean {(data.records.reduce((sum, row) => sum + row.scores[item.id], 0) / data.record_count).toFixed(2)} / 100</small></button>)}<a className="eesi-formula" href="#formula-d"><strong>Formula D ? Real-wage exposure</strong><code>100 ? [alpha ? wage gap + (1 ? alpha) ? U]</code><small>View configuration, score and sample comparison below</small></a></div>
        <FormulaDPanel key={JSON.stringify(data.records)} selected={selected} onEvidence={setFormulaDEvidence} />
        <section className="validation-summary"><h2>{formula?.name}</h2><p>{formula?.rationale}</p><p><strong>Reference:</strong> {data.metadata.reference_period} · {data.metadata.cpi_base}. Normalize each economic input with clip((value − lower) / (upper − lower), 0, 1).</p><p>{Object.entries(data.metadata.bounds).map(([key, values]) => `${key}: ${values.join(' to ')}`).join(' · ')}</p><p>Salary exposure V = reference salary / (reference salary + wages). The LKR {amount(data.metadata.reference_salary)} reference is illustrative.</p></section>
        <section className="validation-summary"><h2>Employee score breakdown</h2><label className="eesi-field">Wage earner<select value={selectedId} onChange={event => setSelectedId(event.target.value)}>{data.records.map(row => <option key={row.sample_id} value={row.sample_id}>{row.sample_id} · {row.economic_month} · LKR {amount(row.salary)}</option>)}</select></label>
          {selected && <><p className="eesi-score">{selected.scores[formulaId].toFixed(2)} <small>/ 100</small></p><p className="muted">Survey: {selected.survey_month}. Economic reference: {selected.economic_month}, using the previous-calendar-month assumption.</p>{Object.entries(selected.breakdown.contributions[formulaId]).map(([key, value]) => <div className="eesi-contribution" key={key}><span>{key.split('_').join(' ')}</span><progress max="100" value={value} aria-label={`${key} score contribution`} /><strong>{value.toFixed(2)} points</strong></div>)}</>}
        </section>
        {selected && <section className="validation-summary"><h2>Financial input availability</h2><div className="summary-grid"><span>Wages / month<strong>LKR {amount(selected.salary)}</strong></span><span>Extra employment pay / month<strong>{amount(selected.extra_pay)}</strong></span><span>Bonus / month equivalent<strong>{amount(selected.bonus_monthly)}</strong></span><span>Total employment income / month<strong>{amount(selected.total_income)}</strong></span><span>Household expenditure / month equivalent<strong>LKR {amount(selected.household_expenditure)}</strong></span><span>Household debt payments / month<strong>{amount(selected.household_debt_payments)}</strong></span></div><p>Extra pay records tips, commissions and overtime; it is not a verified fixed allowance. Household expenditure includes broad survey spending and imputed rent. Debt payments are already included in expenditure. These are not personal living costs and are not included in the candidate indices above.</p><p className="muted">A complete personal-finance EESI needs a defined formula and a defensible way to attribute household finances to an individual. Missing values remain unavailable.</p></section>}
        {scenario && selected && <section className="validation-summary"><h2>What-if calculator</h2><p>Start from {selected.sample_id}. Change wages or economic conditions to compare all three candidates. Reference ranges stay fixed; saved records are unchanged.</p><form onSubmit={event => { event.preventDefault(); void runScenario() }}><div className="eesi-inputs">{(Object.keys(labels) as (keyof HiesScenario)[]).map(key => <label className="eesi-field" key={key}>{labels[key]}<input required type="number" step="any" min={key === 'inflation' ? undefined : key === 'unemployment' ? 0 : 0.000001} max={key === 'unemployment' ? 100 : undefined} value={scenario[key]} onChange={event => { scenarioRequest.current += 1; setScenarioBusy(false); setScenario({ ...scenario, [key]: Number(event.target.value) }); setResult(null) }} /></label>)}</div><button className="primary-button" disabled={scenarioBusy}>{scenarioBusy ? 'Calculating…' : 'Calculate scenario'}</button></form>{scenarioError && <p role="alert" className="upload-error">{scenarioError}</p>}{result && <><div className="summary-grid">{data.metadata.formulas.map(item => <span key={item.id}>{item.name}<strong>{result.scores[item.id].toFixed(2)} / 100</strong><small>Change: {(result.scores[item.id] - selected.scores[item.id]).toFixed(2)} points</small></span>)}</div>{result.warnings.map(warning => <p key={warning} className="eesi-warning">{warning}</p>)}</>}</section>}
        <section className="validation-summary"><h2>Sample comparison</h2><label className="eesi-field">Find sample ID<input value={query} onChange={event => setQuery(event.target.value)} placeholder="HIES19-0001" /></label><div className="mapping-table-wrap"><table><thead><tr><th>Sample ID</th><th>Economic month</th><th>Wages (LKR)</th><th>Household expenditure equivalent (LKR)</th><th>{formula?.name}</th></tr></thead><tbody>{data.records.filter(row => row.sample_id.toLowerCase().includes(query.toLowerCase())).map(row => <tr key={row.sample_id}><td><button className="text-button" onClick={() => setSelectedId(row.sample_id)}>{row.sample_id}</button></td><td>{row.economic_month}</td><td>{amount(row.salary)}</td><td>{amount(row.household_expenditure)}</td><td>{row.scores[formulaId].toFixed(2)}</td></tr>)}</tbody></table></div></section>
      </>}
    </>}
  </section>
}
