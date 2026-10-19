import { useEffect, useState } from 'react'
import { getHiesDataset, type HiesDataset } from './api'

export default function HiesEesiView() {
  const [data, setData] = useState<HiesDataset | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const load = async (importPrepared = false) => {
    setBusy(true); setError('')
    try { setData(await getHiesDataset(importPrepared)) }
    catch (caught) { setError(caught instanceof Error ? caught.message : 'Unable to load HIES data.') }
    finally { setBusy(false) }
  }
  useEffect(() => { void load() }, [])
  const amount = (value: number | null) => value === null ? 'Not reported' : value.toLocaleString('en-LK', { maximumFractionDigits: 2 })
  return <section className="eesi-view">
    <p className="eyebrow">HIES 2019 · Progress presentation</p><h1>Wages and household financial context</h1>
    <p className="muted">A separate sample of adult wage earners, stored privately on this computer.</p>
    {error && <p className="upload-error" role="alert">{error}</p>}
    <div className="cleaning-buttons"><button className="secondary-button" disabled={busy} onClick={() => void load()}>Refresh records</button>
      <button className="primary-button" disabled={busy || !data?.prepared_available} onClick={() => void load(true)}>{busy ? 'Loading…' : data?.record_count ? 'Reimport prepared sample' : 'Import prepared 100-person sample'}</button></div>
    {data && <>
      <div className="summary-grid"><span>Imported wage earners<strong>{data.record_count}</strong></span><span>Complete income components<strong>{data.complete_income_count}</strong></span><span>Reported household debt payments<strong>{data.debt_payment_count}</strong></span></div>
      <div className="eesi-notice"><strong>Exploratory candidate calculations</strong><p>{data.note}</p><p>Monthly-equivalent household expenditure includes broad survey spending and imputed rent. It is not personal living costs. Debt payments are already included in expenditure.</p></div>
      {!data.prepared_available && <p>Prepare the HIES sample before importing it.</p>}
      {data.imported_at && <p className="muted">Last imported: {new Date(data.imported_at).toLocaleString()}</p>}
      {data.record_count > 0 ? <div className="mapping-table-wrap"><table><thead><tr><th>Sample ID</th><th>Economic month</th><th>Wages (LKR)</th><th>Extra pay (LKR)</th><th>Bonus / month equivalent (LKR)</th><th>Household expenditure / month equivalent (LKR)</th><th>Household debt payments (LKR)</th><th>Economic candidate</th><th>Additive candidate</th><th>Interaction candidate</th></tr></thead><tbody>{data.records.map(row => <tr key={row.sample_id}><td>{row.sample_id}</td><td>{row.economic_month}</td><td>{amount(row.salary)}</td><td>{amount(row.extra_pay)}</td><td>{amount(row.bonus_monthly)}</td><td>{amount(row.household_expenditure)}</td><td>{amount(row.household_debt_payments)}</td><td>{row.scores.economic.toFixed(2)}</td><td>{row.scores.additive.toFixed(2)}</td><td>{row.scores.interaction.toFixed(2)}</td></tr>)}</tbody></table></div> : <p>No HIES records imported yet. Import the prepared sample to begin.</p>}
    </>}
  </section>
}
