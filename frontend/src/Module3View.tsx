import { familyName } from './eesiFamilies'
import ImportedSourceView from './ImportedSourceView'
import { useEffect, useState } from 'react'
import { getModule3PilotRecords, type Module3PilotRecord } from './api'
import { getModule3Contract, getModule3Evaluation, getModule3ModelStatus, predictModule3, type Module3Contract, type Module3Evaluation, type Module3ModelStatus, type Module3Prediction } from './api'

const sampleRecord = {
  Age: 58,
  MonthlyIncome: 111166,
  OverTime: 'No',
  JobSatisfaction: 2,
  JobLevel: 3,
  YearsAtCompany: 6,
  Department: 'Research & Development',
  EESI: 37.5,
}

export default function Module3View() {
  const [contract, setContract] = useState<Module3Contract | null>(null)
  const [status, setStatus] = useState<Module3ModelStatus | null>(null)
  const [record, setRecord] = useState(sampleRecord)
  const [prediction, setPrediction] = useState<Module3Prediction | null>(null)
  const [evaluation, setEvaluation] = useState<Module3Evaluation | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [loading, setLoading] = useState(true)
  const [employees, setEmployees] = useState<Module3PilotRecord[]>([])
  const [selectedId, setSelectedId] = useState('')

  const load = async () => {
    setLoading(true); setError(''); setPrediction(null); setEvaluation(null)
    try {
      const [loadedContract, loadedStatus] = await Promise.all([getModule3Contract(), getModule3ModelStatus()])
      setContract(loadedContract); setStatus(loadedStatus)
      if (loadedStatus.model_available) {
        const pilot = await getModule3PilotRecords()
        setEmployees(pilot.records)
        if (pilot.records[0]) { setRecord(pilot.records[0].record); setSelectedId(pilot.records[0].employee_id) }
      }
    } catch (caughtError) { setError(caughtError instanceof Error ? caughtError.message : 'Unable to load Module 3 status.') }
    finally { setLoading(false) }
  }
  useEffect(() => { void load() }, [])

  const updateValue = (field: keyof typeof sampleRecord, value: string) => {
    setPrediction(null); setSelectedId('')
    const numericFields = ['Age', 'MonthlyIncome', 'JobSatisfaction', 'JobLevel', 'YearsAtCompany', 'EESI']
    setRecord((current) => ({ ...current, [field]: numericFields.includes(field) ? Number(value) : value }))
  }

  const runPrediction = async () => {
    setBusy(true); setError(''); setPrediction(null)
    try { setPrediction(await predictModule3(record)) }
    catch (caughtError) { setError(caughtError instanceof Error ? caughtError.message : 'Prediction failed.') }
    finally { setBusy(false) }
  }

  const loadEvaluation = async () => {
    setBusy(true); setError('')
    try { setEvaluation(await getModule3Evaluation()) }
    catch (caughtError) { setError(caughtError instanceof Error ? caughtError.message : 'Evaluation report is unavailable.') }
    finally { setBusy(false) }
  }

  return <section className="module3-view">
    <p className="eyebrow">Module 3 · integrated prediction pipeline</p>
    <h1>Employee turnover prediction</h1>
    <details className="validation-summary"><summary>Use additional imported datasets</summary><ImportedSourceView stage="prediction" /></details>
    <button className="secondary-button" disabled={loading || busy} onClick={() => void load()}>{loading ? 'Loading model…' : 'Refresh model status'}</button>
    <p className="muted">Uses the saved model's original EESI formula. Extended B/C and the 70/30 experiment are not prediction inputs.</p>
    {error && <p className="upload-error" role="alert">{error}</p>}
    {!loading && status && !status.model_available && <p className="muted">Prepare the demo with <code>backend\.venv\Scripts\python.exe scripts/prepare_module3_demo.py</code> from the project root, then refresh model status.</p>}
    <div className="module3-grid">
      <article className="validation-summary"><h2>Integration contract</h2>{contract ? <><p><strong>Contract:</strong> {contract.contract_version}</p><p><strong>EESI field:</strong> {contract.eesi.column}</p><p><strong>Supported formulas:</strong> {contract.eesi.supported_formula_ids.join(', ')}</p><p><strong>Model features:</strong> {contract.feature_columns.join(', ')}</p></> : <p className="muted">Loading contract…</p>}</article>
      <article className="validation-summary"><h2>Model status</h2>{status ? <><p className={status.model_available ? 'status-ready' : 'status-waiting'}>{status.model_available ? 'Model artifact available' : 'Model artifact unavailable'}</p><p>{status.message}</p>{status.eesi_integration?.enabled && <p><strong>EESI provenance:</strong> {status.eesi_integration.formula_id ? familyName(status.eesi_integration.formula_id) : 'not recorded'} · {status.eesi_integration.formula_version ?? 'not recorded'}</p>}</> : <p className="muted">Checking local model…</p>}</article>
    </div>
    <article className="validation-summary module3-form"><h2>Prediction input</h2><p className="muted">Select a synthetic employee to load HR inputs and the calculated EESI matching the saved model's formula. HIES respondents have no attrition labels and are kept separate.</p>
      {!!employees.length && <label className="eesi-field">Synthetic pilot employee<select disabled={busy || loading} value={selectedId} onChange={event => { const employee = employees.find(item => item.employee_id === event.target.value); if (employee) { setRecord(employee.record); setSelectedId(employee.employee_id); setPrediction(null) } }}><option value="" disabled>Custom inputs</option>{employees.map(employee => <option key={employee.employee_id} value={employee.employee_id}>{employee.employee_id} · {employee.month}</option>)}</select></label>}
      {!selectedId && <p className="muted">Custom inputs: supply EESI using the model's recorded formula and reference profile. Changing other fields does not recalculate a manually supplied EESI.</p>}
      <form onSubmit={event => { event.preventDefault(); void runPrediction() }}><fieldset disabled={busy || loading} style={{ border: 0, padding: 0, margin: 0 }}><div className="module3-fields">
      <label>Age<input required type="number" min="14" max="100" value={record.Age} onChange={(event) => updateValue('Age', event.target.value)} /></label>
      <label>Monthly income (LKR)<input required type="number" min="0" value={record.MonthlyIncome} onChange={(event) => updateValue('MonthlyIncome', event.target.value)} /></label>
      <label>Overtime<select value={record.OverTime} onChange={(event) => updateValue('OverTime', event.target.value)}><option>Yes</option><option>No</option></select></label>
      <label>Job satisfaction<input required type="number" min="1" max="4" value={record.JobSatisfaction} onChange={(event) => updateValue('JobSatisfaction', event.target.value)} /></label>
      <label>Job level<input required type="number" min="1" max="5" value={record.JobLevel} onChange={(event) => updateValue('JobLevel', event.target.value)} /></label>
      <label>Years at company<input required type="number" min="0" value={record.YearsAtCompany} onChange={(event) => updateValue('YearsAtCompany', event.target.value)} /></label>
      <label>Department<input required value={record.Department} onChange={(event) => updateValue('Department', event.target.value)} /></label>
      <label>Original EESI (model formula)<input required type="number" min="0" max="100" step="any" value={record.EESI} onChange={(event) => updateValue('EESI', event.target.value)} /></label>
    </div></fieldset><div className="cleaning-buttons"><button type="submit" className="primary-button" disabled={!status?.model_available || busy || loading}>{busy ? 'Loading result…' : 'Predict turnover class'}</button><button type="button" className="secondary-button" disabled={!status?.model_available || busy || loading} onClick={loadEvaluation}>Show held-out evaluation</button></div></form></article>
    {prediction && <article className="validation-summary success"><h2>Model prediction</h2><p className="module3-class">Predicted class: <strong>{prediction.predicted_class}</strong></p><div className="summary-grid">{Object.entries(prediction.class_probabilities).map(([label, probability]) => <span key={label}>{label}<strong>{(probability * 100).toFixed(2)}%</strong></span>)}</div><p>{prediction.interpretation}</p></article>}
    {evaluation && <article className="validation-summary"><h2>Held-out evaluation</h2><p><strong>Split:</strong> {evaluation.dataset_split.method}; {evaluation.dataset_split.train_rows} training / {evaluation.dataset_split.heldout_rows} held-out records.</p><div className="summary-grid">{Object.entries(evaluation.metrics).map(([metric, value]) => <span key={metric}>{metric.replace(/_/g, ' ')}<strong>{value === null ? 'Not available' : Number(value).toFixed(3)}</strong></span>)}</div><p><strong>Confusion matrix:</strong> {JSON.stringify(evaluation.confusion_matrix)} for classes {evaluation.confusion_matrix_labels.join(', ')}.</p><ul>{evaluation.limitations.map((limitation) => <li key={limitation}>{limitation}</li>)}</ul></article>}
  </section>
}
