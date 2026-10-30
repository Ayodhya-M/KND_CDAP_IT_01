import { useEffect, useRef, useState } from 'react'
import { requestFormulaD, type FormulaDComparison, type FormulaDConfig, type FormulaDResult, type HiesRecord } from './api'

const fixed = (n: number) => n.toFixed(2)
export default function FormulaDPanel({ selected, onEvidence }: { selected: HiesRecord | undefined; onEvidence: (value: unknown) => void }) {
  const [reference, setReference] = useState('')
  const [alpha, setAlpha] = useState('0.5')
  const [source, setSource] = useState('')
  const [justification, setJustification] = useState('')
  const [comparison, setComparison] = useState<FormulaDComparison | null>(null)
  const [result, setResult] = useState<FormulaDResult | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [inputs, setInputs] = useState({ employee_wage: '', ncpi: '', unemployment_rate: '' })
  const revision = useRef(0)
  const scenarioRevision = useRef(0)
  const configuration = useRef<FormulaDConfig | null>(null)
  useEffect(() => {
    scenarioRevision.current += 1
    setInputs({ employee_wage: selected ? String(selected.salary) : '', ncpi: selected ? String(selected.cpi) : '', unemployment_rate: selected ? String(selected.unemployment) : '' })
    setResult(null)
  }, [selected])
  useEffect(() => {
    onEvidence({ comparison: comparison ?? { enabled: false, message: 'Formula D disabled: reference income must be configured and applied.' }, scenario_inputs: inputs, scenario_result: result })
  }, [comparison, result, inputs, onEvidence])
  function invalidate() {
    revision.current += 1; scenarioRevision.current += 1
    configuration.current = null; setComparison(null); setResult(null); setError(''); setBusy(false)
  }
  async function configure() {
    const request = ++revision.current
    setBusy(true); setError('')
    const config = { reference_income_2013: reference.trim() ? Number(reference) : null, alpha: Number(alpha), reference_income_source: source, reference_income_justification: justification }
    try {
      if (!alpha.trim() || !Number.isFinite(config.alpha) || (reference.trim() && !Number.isFinite(config.reference_income_2013))) throw new Error('Enter finite numeric configuration values.')
      const next = await requestFormulaD<FormulaDComparison>('hies/formula-d', config)
      if (request === revision.current) { configuration.current = config; setComparison(next); setResult(null) }
    } catch (caught) { if (request === revision.current) setError(caught instanceof Error ? caught.message : 'Calculation failed.') }
    finally { if (request === revision.current) setBusy(false) }
  }
  async function scenario() {
    const config = configuration.current
    if (!config || !comparison?.enabled) return
    const request = ++scenarioRevision.current
    setResult(null); setError('')
    try {
      if (Object.values(inputs).some(value => !value.trim() || !Number.isFinite(Number(value)))) throw new Error('All scenario inputs are required and must be finite numbers.')
      const next = await requestFormulaD<FormulaDResult>('formula-d/scenario', { ...config, ...Object.fromEntries(Object.entries(inputs).map(([key, value]) => [key, Number(value)])) })
      if (request === scenarioRevision.current) setResult(next)
    } catch (caught) { if (request === scenarioRevision.current) setError(caught instanceof Error ? caught.message : 'Scenario failed.') }
  }
  const baseline = comparison?.records.find(row => row.sample_id === selected?.sample_id)
  const details = (value: FormulaDResult) => <div className="summary-grid"><span>Real wage (monthly 2013 LKR)<strong>{fixed(value.real_wage)}</strong></span><span>Wage inadequacy (0â€“1)<strong>{fixed(value.wage_inadequacy)}</strong></span><span>Normalized unemployment (0â€“1)<strong>{fixed(value.normalized_unemployment)}</strong></span><span>Formula D score<strong>{fixed(value.score)} / 100</strong></span></div>
  return <section id="formula-d" className="validation-summary">
    <h2>D ? Real-Wage / Purchasing Power</h2>
    <p>Proposed, unvalidated research index. This is not a validated psychological financial stress scale or a turnover probability.</p>
    <code>100 Ã— [alpha Ã— wage inadequacy + (1 âˆ’ alpha) Ã— normalized unemployment]</code>
    <p>Real wage = wage Ã— 100 / NCPI (2013=100). Wage inadequacy = clip(1 âˆ’ real wage / reference income, 0, 1). HIES 2019 unemployment normalization = clip((unemployment âˆ’ 4.5) / (5.1 âˆ’ 4.5), 0, 1).</p>
    <p>Version: real-wage-hies2019-v1. RW = 100 ? S/CPI; G = clip((Z ? RW)/Z, 0, 1). Default alpha = 0.5 gives D = 100 ? (0.5G + 0.5U). Existing alpha configuration is preserved. Purpose: compare purchasing power with a reference real income Z and combine the shortfall with unemployment.</p>
    <form onSubmit={event => { event.preventDefault(); void configure() }}><div className="eesi-inputs">
      <label className="eesi-field">Illustrative reference income (monthly 2013 purchasing-power LKR)<input type="number" step="any" min="0.000000001" value={reference} placeholder="No threshold configured" onChange={event => { invalidate(); setReference(event.target.value) }} /></label>
      <label className="eesi-field">Alpha (0â€“1)<input required type="number" min="0" max="1" step="any" value={alpha} onChange={event => { invalidate(); setAlpha(event.target.value) }} /></label>
      <label className="eesi-field">Reference income source<input value={source} placeholder="Not provided; illustrative only" onChange={event => { invalidate(); setSource(event.target.value) }} /></label>
      <label className="eesi-field">Reference income justification<input value={justification} placeholder="Record the reason for this threshold" onChange={event => { invalidate(); setJustification(event.target.value) }} /></label>
    </div><button className="primary-button" disabled={busy}>{busy ? 'Calculatingâ€¦' : 'Apply Formula D configuration'}</button></form>
    <p role="status">{comparison?.message ?? 'Formula D is disabled until a reference income is configured and applied.'}</p>
    <p className="muted">The threshold and weight remain illustrative. No defensible income benchmark has been established. Parameters apply only to the HIES 2019 demonstration; other CPI base years and periods are unsupported. Configuration is session-only and is recorded in downloads.</p>
    {error && <p role="alert" className="upload-error">{error}</p>}
    {comparison?.enabled && <><p><strong>Formula D sample mean: {comparison.records.length ? fixed(comparison.records.reduce((sum, row) => sum + row.score, 0) / comparison.records.length) : 'No records'} / 100</strong></p>
      {baseline && <><h3>{selected?.sample_id} Â· Formula D breakdown</h3>{details(baseline)}</>}
      <h3>Formula D scenario testing</h3><form onSubmit={event => { event.preventDefault(); void scenario() }}><div className="eesi-inputs">{(Object.keys(inputs) as (keyof typeof inputs)[]).map(key => <label key={key} className="eesi-field">{ { employee_wage: 'Monthly employee wage (LKR)', ncpi: 'NCPI (2013=100)', unemployment_rate: 'National unemployment (%)' }[key]}<input required type="number" step="any" min={key === 'ncpi' ? '0.000000001' : '0'} value={inputs[key]} onChange={event => { scenarioRevision.current += 1; setResult(null); setInputs({ ...inputs, [key]: event.target.value }) }} /></label>)}</div><button className="primary-button">Calculate Formula D scenario</button></form>
      {result && <>{details(result)}{baseline && <p>Change from selected record: {fixed(result.score - baseline.score)} points.</p>}</>}
      <div className="mapping-table-wrap"><table><thead><tr><th>Sample ID</th><th>Real wage (2013 LKR)</th><th>Wage inadequacy</th><th>Normalized unemployment</th><th>Formula D / 100</th></tr></thead><tbody>{comparison.records.map(row => <tr key={row.sample_id}><td>{row.sample_id}</td><td>{fixed(row.real_wage)}</td><td>{fixed(row.wage_inadequacy)}</td><td>{fixed(row.normalized_unemployment)}</td><td>{fixed(row.score)}</td></tr>)}</tbody></table></div>
    </>}
  </section>
}
