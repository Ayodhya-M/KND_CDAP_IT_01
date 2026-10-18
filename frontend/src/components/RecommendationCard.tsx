import type { Module4Recommendation } from '../api'
import { formatFeatureName } from './RiskFactorsList'

function statusClass(level: string) {
  const normalized = level.toLowerCase()
  return ['low', 'medium', 'high'].includes(normalized) ? normalized : 'neutral'
}

export function RecommendationCard({ recommendation, rank }: { recommendation: Module4Recommendation; rank: number }) {
  return <article className="recommendation-card">
    <div className="recommendation-header">
      <span className="recommendation-number" aria-label={`Rank ${rank}`}>{rank}</span>
      <div><h3>{recommendation.title}</h3><p>{recommendation.category} · {formatFeatureName(recommendation.related_factor)}</p></div>
      <div className="recommendation-priority"><span className={`status-badge ${statusClass(recommendation.priority_level)}`}>{recommendation.priority_level}</span><strong>{recommendation.priority_score.toFixed(1)}</strong><small>/ 100</small></div>
    </div>
    <details className="recommendation-details">
      <summary>View rationale and suggested action</summary>
      <div className="recommendation-copy"><h4>Why this is recommended</h4><p>{recommendation.explanation}</p></div>
      <div className="suggested-action"><h4>Suggested HR Action</h4><p>{recommendation.suggested_action}</p></div>
    </details>
  </article>
}
