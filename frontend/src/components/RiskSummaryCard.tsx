type RiskSummaryCardProps = {
  label: string
  value: string
  level: string
  description: string
}

function statusClass(level: string) {
  const normalized = level.toLowerCase()
  return ['low', 'medium', 'high'].includes(normalized) ? normalized : 'neutral'
}

export function RiskSummaryCard({ label, value, level, description }: RiskSummaryCardProps) {
  return <article className="risk-summary-card">
    <p className="summary-label">{label}</p>
    <strong className="summary-value">{value}</strong>
    <span className={`status-badge ${statusClass(level)}`}>{level}</span>
    <small>{description}</small>
  </article>
}
