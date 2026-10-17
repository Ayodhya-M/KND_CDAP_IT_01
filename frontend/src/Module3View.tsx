import { useEffect, useState } from 'react'
import {
  getModule3Contract,
  getModule3ModelStatus,
  type Module3Contract,
  type Module3ModelStatus,
} from './api'

export default function Module3View() {
  const [contract, setContract] = useState<Module3Contract | null>(null)
  const [status, setStatus] = useState<Module3ModelStatus | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const [contractResult, statusResult] = await Promise.all([
          getModule3Contract(),
          getModule3ModelStatus(),
        ])
        setContract(contractResult)
        setStatus(statusResult)
      } catch (caughtError) {
        setError(caughtError instanceof Error ? caughtError.message : 'Unable to load Module 3 status.')
      } finally {
        setLoading(false)
      }
    }
    void load()
  }, [])

  return <section className="upload-view">
    <p className="eyebrow">Module 3</p>
    <h1>Turnover prediction</h1>
    <p className="muted">Inspect the current model and integration contract. Predictions require an approved local model artifact.</p>
    {loading && <p className="muted">Loading Module 3 status…</p>}
    {error && <p className="upload-error" role="alert">{error}</p>}
    {status && <section className={`validation-summary ${status.model_available ? 'success' : 'validation_failed'}`}>
      <h2>{status.model_available ? 'Model artifact available' : 'Model artifact unavailable'}</h2>
      <p>{status.message}</p>
      <div className="summary-grid">
        <span>Dataset status<strong>{status.dataset_kind}</strong></span>
        <span>Model<strong>{status.model_name ?? 'Not available'}</strong></span>
        <span>Features<strong>{status.feature_columns?.length ?? 0}</strong></span>
      </div>
    </section>}
    {contract && <section className="validation-summary success">
      <h2>Integration contract</h2>
      <p>{contract.purpose}</p>
      <p><strong>Contract version:</strong> {contract.contract_version}</p>
      <p><strong>Required features:</strong> {contract.feature_columns.join(', ')}</p>
      <p><strong>EESI formula choices:</strong> {contract.eesi.supported_formula_ids.join(', ')}</p>
    </section>}
  </section>
}
