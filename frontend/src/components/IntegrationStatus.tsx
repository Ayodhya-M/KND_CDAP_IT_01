import type { Module4Metadata } from '../api'

const sourceLabels: Record<string, string> = {
  mock: 'Deterministic mock fixtures',
  module2_calculated_pilot: 'Calculated pilot EESI',
  module3_synthetic_model: 'Saved synthetic pilot model',
  module2: 'Configured Module 2 provider',
  module3: 'Configured Module 3 provider',
}

function sourceLabel(source: string) {
  return sourceLabels[source.toLowerCase()] ?? source.replace(/_/g, ' ')
}

export function IntegrationStatus({ metadata }: { metadata: Module4Metadata }) {
  const isMock = metadata.data_mode === 'mock_integration'
  const isDemo = metadata.data_mode === 'synthetic_demo_integration'
  return <aside className={`integration-status ${isMock ? 'mock' : 'integrated'}`} aria-labelledby="integration-status-heading">
    <div className="numbered-heading"><span>05</span><div><p className="eyebrow">Research provenance</p><h2 id="integration-status-heading">{isDemo ? 'Connected Synthetic Pilot' : isMock ? 'Development Integration Mode' : 'Integrated Provider Mode'}</h2></div></div>
    <p>{isDemo
      ? 'Module 1 supplies the stored pilot employee and mapped economic context. Module 2 calculates EESI, while Module 3 supplies a probability from the saved synthetic pilot model.'
      : isMock
        ? 'Module 1 employee data comes from the project database. Module 2 and Module 3 currently supply deterministic development fixtures.'
        : 'The dashboard is displaying results returned by the configured module providers.'}</p>
    <p className="muted">Uses original EESI provider results. Extended B/C and the earlier 70/30 experiment do not change this analysis.</p>
    <dl className="source-list">
      <div><dt>Module 1</dt><dd>{isDemo ? 'Supabase · stored synthetic pilot record' : 'Supabase project database'}</dd></div>
      <div><dt>Module 2</dt><dd>{sourceLabel(metadata.module2_source)}</dd></div>
      <div><dt>Module 3</dt><dd>{sourceLabel(metadata.module3_source)}</dd></div>
      <div><dt>Module 4 rules</dt><dd>{metadata.recommendation_rule_version}</dd></div>
    </dl>
    <p className="backend-disclaimer"><strong>Provider notice:</strong> {metadata.disclaimer}</p>
    <div className="research-limitations">
      <p><strong>Priority method:</strong> {metadata.priority_method}</p>
      <p><strong>Sensitivity analysis:</strong> {metadata.sensitivity_notice}</p>
      <p><strong>Validation limitation:</strong> The synthetic model, recommendation rules, eligibility boundaries, weights, and priority bands are not final validated research findings.</p>
    </div>
  </aside>
}
