import type { Module4Recommendation } from '../api'
import { formatFeatureName } from './RiskFactorsList'

function statusClass(level: string) {
  const normalized = level.toLowerCase()
  return ['low', 'medium', 'high'].includes(normalized) ? normalized : 'neutral'
}

export function RecommendationCard({ recommendation, rank }: { recommendation: Module4Recommendation; rank: number }) {
  return <article className="recommendation-card">
    <div className="recommendation-header">
      <div><p className="recommendation-rank">Recommendation {rank}</p><h3>{recommendation.title}</h3></div>
      <span className={`status-badge ${statusClass(recommendation.priority_level)}`}>
        {recommendation.priority_level} Priority
      </span>
    </div>
    <dl className="recommendation-meta">
      <div><dt>Category</dt><dd>{recommendation.category}</dd></div>
      <div><dt>Related Risk Factor</dt><dd>{formatFeatureName(recommendation.related_factor)}</dd></div>
      <div><dt>Priority Score</dt><dd>{recommendation.priority_score.toFixed(1)} / 100</dd></div>
    </dl>
    <div className="recommendation-copy"><h4>Why this is recommended</h4><p>{recommendation.explanation}</p></div>
    <div className="suggested-action"><h4>Suggested HR Action</h4><p>{recommendation.suggested_action}</p></div>
  </article>
}
