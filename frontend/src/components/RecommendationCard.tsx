import type { Module4Recommendation } from '../api'
import { formatFeatureName } from './RiskFactorsList'

function statusClass(level: string) {
  const normalized = level.toLowerCase()
  return ['low', 'medium', 'high'].includes(normalized) ? normalized : 'neutral'
}

export function RecommendationCard({ recommendation, rank }: { recommendation: Module4Recommendation; rank: number }) {
  const breakdown = recommendation.priority_breakdown
  const rows = [
    ['Turnover risk', 'turnover_risk'],
    ['Factor contribution', 'factor_contribution'],
    ['Economic pressure', 'economic_pressure'],
    ['Intervention relevance', 'intervention_relevance'],
  ] as const
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
      <div className="recommendation-audit">
        <h4>Priority calculation</h4>
        <p className="calculation-formula">{breakdown.formula}</p>
        <div className="priority-breakdown" role="table" aria-label={`${recommendation.title} priority calculation`}>
          <div className="priority-breakdown-heading" role="row"><span>Component</span><span>Input</span><span>Weight</span><span>Points</span></div>
          {rows.map(([label, key]) => <div role="row" key={key}><span>{label}</span><span>{breakdown.inputs[key].toFixed(3)}</span><span>{breakdown.weights[key].toFixed(2)}</span><span>{(breakdown.weighted_components[key] * 100).toFixed(2)}</span></div>)}
          <div className="priority-breakdown-total" role="row"><strong>Total</strong><span /><span /><strong>{breakdown.score.toFixed(2)}</strong></div>
        </div>
        <h4>Exploratory weight sensitivity</h4>
        <p>Small one-at-a-time weight perturbations test ranking stability; they are not validated alternative formulas.</p>
        <div className="sensitivity-list">{recommendation.sensitivity_analysis.map(item => <div key={item.scenario_id}><span>{item.label}</span><strong>{item.score.toFixed(2)} · Rank {item.rank}</strong></div>)}</div>
        <h4>Rule traceability</h4>
        <p>{recommendation.traceability}</p>
      </div>
    </details>
  </article>
}
