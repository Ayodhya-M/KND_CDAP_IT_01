import { useEffect, useRef, useState } from 'react'
import { analyseSource, getSourceRecords, getSources, type SourceAnalysis, type SourceDataset } from './sourceDataApi'

export default function ImportedSourceView({ stage = 'all' }: { stage?: 'all' | 'eesi' | 'prediction' | 'retention' }) {
  const [datasets, setDatasets] = useState<SourceDataset[]>([])
  const [datasetId, setDatasetId] = useState('')
  const [records, setRecords] = useState<{ record_id: string; month: string | null }[]>([])
  const [recordId, setRecordId] = useState('')
  const [result, setResult] = useState<SourceAnalysis | null>(null)
  const [scenario, setScenario] = useState<SourceAnalysis | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const requestId = useRef(0)
  const dataset = datasets.find(item => item.id === datasetId)
  useEffect(() => {
    let active = true
    getSources().then(response => {
      if (!active) return
      setDatasets(response.datasets)
      const saved = sessionStorage.getItem('additional-source-id')
      setDatasetId(response.datasets.find(item => item.id === saved)?.id ?? response.datasets.find(item => item.eesi_available)?.id ?? response.datasets[0]?.id ?? '')
    }).catch(caught => { if (active) setError(caught instanceof Error ? caught.message : 'Unable to load sources.') })
    return () => { active = false }
  }, [])
  useEffect(() => {
    requestId.current += 1
    setResult(null); setScenario(null); setRecords([]); setRecordId('')
    if (!datasetId) return
    let active = true
    sessionStorage.setItem('additional-source-id', datasetId)
    getSourceRecords(datasetId).then(response => {
      if (!active) return
      setRecords(response.records)
      setRecordId(response.records[0]?.record_id ?? '')
    }).catch(caught => { if (active) setError(caught instanceof Error ? caught.message : 'Unable to load records.') })
    return () => { active = false }
  }, [datasetId])
  useEffect(() => {
    setScenario(null); setResult(null)
    if (!datasetId || !recordId) return
    const version = ++requestId.current
    setBusy(true); setError('')
    analyseSource(datasetId, recordId).then(value => { if (version === requestId.current) setResult(value) })
      .catch(caught => { if (version === requestId.current) setError(caught instanceof Error ? caught.message : 'Analysis failed.') })
      .finally(() => { if (version === requestId.current) setBusy(false) })
    return () => { requestId.current += 1 }
  }, [datasetId, recordId])
  const runScenario = async () => {
    if (!result || !dataset) return
    const field = dataset.eesi_available ? 'Monthly_Base_Salary_LKR' : 'MonthlyIncome'
    const salary = Number(result.inputs[field]) * 1.1
    const version = ++requestId.current
    setBusy(true); setError(''); setScenario(null)
    try {
      const value = await analyseSource(datasetId, recordId, salary)
      if (version === requestId.current) setScenario(value)
    } catch (caught) { if (version === requestId.current) setError(caught instanceof Error ? caught.message : 'Scenario failed.') }
    finally { if (version === requestId.current) setBusy(false) }
  }
  return <section className="upload-view">
    <p className="eyebrow">Module 1 · Additional sources · Private local storage</p>
    <h1>Source-aware employee data</h1><p className="muted">Only relevant columns are retained. Source cohorts, currencies, rating scales and target meanings stay separate.</p>
    {error && <p role="alert" className="upload-error">{error}</p>}
    {!datasets.length && !error && <p>No additional sources are imported yet.</p>}
    {!!datasets.length && <div className="eesi-inputs"><label className="eesi-field">Dataset<select value={datasetId} disabled={busy} onChange={event => setDatasetId(event.target.value)}>{datasets.map(item => <option value={item.id} key={item.id}>{item.name}</option>)}</select></label><label className="eesi-field">Record<select value={recordId} disabled={busy || !records.length} onChange={event => setRecordId(event.target.value)}>{records.map(item => <option key={item.record_id} value={item.record_id}>{item.record_id}{item.month ? ` · ${item.month} scenario` : ''}</option>)}</select></label></div>}
    {dataset && <>
      <div className="summary-grid"><span>Imported records<strong>{dataset.record_count}</strong></span><span>Target<strong>{dataset.target_label}</strong></span><span>Economic context<strong>{dataset.eesi_available ? '2019 scenario months' : 'Not supplied'}</strong></span></div>
      <details><summary>Retained fields and source details</summary><p>{dataset.retained_fields.join(', ')}</p><p>Source: {dataset.source_file} · {dataset.source_rows} source rows · currency: {dataset.currency}.</p><p>{dataset.kind}. {dataset.warning}</p><p>{dataset.date_note}</p><p>These datasets are stored separately from the Supabase HR pilot and HIES.</p></details>
    </>}
    {busy && <p role="status">Running the source-specific pipeline…</p>}
    {result && <>
      {(stage === 'all' || stage === 'eesi') && <section className="validation-summary"><h2>Module 2 · EESI</h2><p>{result.dataset.eesi_note}</p>{result.eesi ? <><div className="summary-grid">{Object.entries(result.eesi.scores).map(([name, score]) => <span key={name}>{name}<strong>{score.toFixed(2)} / 100</strong></span>)}</div><p>Prediction uses the additive candidate with version {result.eesi.version}. Expenses and debt are not included in these three formulas.</p></> : <p>Unavailable: benchmark observation month and verified currency/geography are missing. No dates or Sri Lankan economic values were invented.</p>}</section>}
      {(stage === 'all' || stage === 'prediction') && <section className="validation-summary"><h2>Module 3 · {result.prediction.target_label}</h2><p>Predicted class: <strong>{result.prediction.predicted_class}</strong></p><div className="summary-grid">{Object.entries(result.prediction.class_probabilities).map(([label, probability]) => <span key={label}>{label}<strong>{(probability * 100).toFixed(2)}%</strong></span>)}</div><p>Source-specific model · {result.evaluation.split.train_rows} training / {result.evaluation.split.heldout_rows} held-out records. This is a software demonstration, not validated workforce performance.</p></section>}
      {(stage === 'all' || stage === 'retention') && <section className="validation-summary"><h2>Module 4 · Prototype options</h2><p>Options are ranked by positive probability differences under input probes. They are not causal effects or validated risk bands.</p>{result.recommendations.length ? <ul>{result.recommendations.map(action => <li key={action.title}><strong>{action.title}</strong> · model sensitivity {action.sensitivity_pp.toFixed(2)} percentage points</li>)}</ul> : <p>No supported positive input sensitivity was found; no recommendation is fabricated.</p>}</section>}
      <section className="validation-summary"><h2>Read-only pipeline check</h2><button type="button" disabled={busy} className="secondary-button" onClick={() => void runScenario()}>Compare salary +10% scenario</button>{scenario && <p>Yes-class model probability: {(result.prediction.class_probabilities.Yes * 100).toFixed(2)}% → {(scenario.prediction.class_probabilities.Yes * 100).toFixed(2)}%. {scenario.eesi ? `Additive EESI: ${result.eesi?.scores.additive.toFixed(2)} → ${scenario.eesi.scores.additive.toFixed(2)}.` : 'EESI remains unavailable.'} Saved records are unchanged.</p>}</section>
      <details><summary>Selected record inputs</summary><div className="mapping-table-wrap"><table><thead><tr><th>Field</th><th>Source value</th></tr></thead><tbody>{Object.entries(result.inputs).map(([key, value]) => <tr key={key}><td>{key}</td><td>{typeof value === 'number' ? value.toLocaleString() : value}</td></tr>)}</tbody></table></div></details>
    </>}
  </section>
}
