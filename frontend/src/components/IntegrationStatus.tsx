import type { Module4Metadata } from '../api'

function sourceLabel(source: string) {
  return source.toLowerCase() === 'mock' ? 'Mock Integration' : source
}

export function IntegrationStatus({ metadata }: { metadata: Module4Metadata }) {
  const isMock = metadata.data_mode === 'mock_integration'
  return <aside className={`integration-status ${isMock ? 'mock' : 'integrated'}`} aria-labelledby="integration-status-heading">
    <div>
      <p className="eyebrow">Data provenance</p>
      <h2 id="integration-status-heading">{isMock ? 'Development Integration Mode' : 'Integrated Data Mode'}</h2>
      <p>{isMock
        ? 'Module 1 employee data is retrieved from the project database. Module 2 economic-pressure and Module 3 prediction outputs are currently deterministic development fixtures used to validate the Module 4 decision-support pipeline.'
        : 'The dashboard is displaying results supplied through the integrated module providers.'}</p>
    </div>
    <dl className="source-list">
      <div><dt>Module 1</dt><dd>Real Project Data</dd></div>
      <div><dt>Module 2</dt><dd>{sourceLabel(metadata.module2_source)}</dd></div>
      <div><dt>Module 3</dt><dd>{sourceLabel(metadata.module3_source)}</dd></div>
    </dl>
    <p className="backend-disclaimer"><strong>Backend notice:</strong> {metadata.disclaimer}</p>
  </aside>
}
