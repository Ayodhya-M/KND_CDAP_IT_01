import type { Module4Recommendation } from '../api'
import { formatFeatureName } from './RiskFactorsList'

function statusClass(level: string) {
  const normalized = level.toLowerCase()
  return ['low', 'medium', 'high'].includes(normalized) ? normalized : 'neutral'
}

const PRIORITY_ROWS = [
  ['Turnover risk', 'turnover_risk'],
  ['Factor contribution', 'factor_contribution'],
  ['Economic pressure', 'economic_pressure'],
  ['Intervention relevance', 'intervention_relevance'],
] as const

export function RecommendationCard({ recommendation, rank }: { recommendation: Module4Recommendation; rank: number }) {
  const breakdown = recommendation.priority_breakdown

  return <article className="recommendation-card">
    <div className="recommendation-header">
      <span className="recommendation-number" aria-label={`Recommendation rank ${rank}`}>{rank}</span>
      <div><h3>{recommendation.title}</h3><p>{recommendation.category} · Related factor: {formatFeatureName(recommendation.related_factor)}</p></div>
      <div className="recommendation-priority"><span className={`status-badge ${statusClass(recommendation.priority_level)}`}>{recommendation.priority_level}</span><strong>{recommendation.priority_score.toFixed(1)}</strong><small>/ 100</small></div>
    </div>
    <details className="recommendation-details">
      <summary>Explanation, calculation and research traceability</summary>
      <div className="recommendation-copy"><h4>Why this option was generated</h4><p>{recommendation.explanation}</p></div>
      <div className="suggested-action"><h4>Suggested HR review</h4><p>{recommendation.suggested_action}</p></div>
      <div className="recommendation-audit">
        <div className="rule-identity"><span>Rule ID <strong>{recommendation.recommendation_id}</strong></span><span>Catalogue <strong>{recommendation.rule_version}</strong></span></div>
        <h4>Priority calculation</h4>
        <p className="calculation-formula">{breakdown.formula}</p>
        <div className="priority-breakdown" role="table" aria-label={`${recommendation.title} priority calculation`}>
          <div className="priority-breakdown-heading" role="row"><span role="columnheader">Component</span><span role="columnheader">Input</span><span role="columnheader">Weight</span><span role="columnheader">Points</span></div>
          {PRIORITY_ROWS.map(([label, key]) => <div role="row" key={key}><span role="cell">{label}</span><span role="cell">{breakdown.inputs[key].toFixed(3)}</span><span role="cell">{breakdown.weights[key].toFixed(2)}</span><span role="cell">{(breakdown.weighted_components[key] * 100).toFixed(2)}</span></div>)}
          <div className="priority-breakdown-total" role="row"><strong role="cell">Total</strong><span role="cell" /><span role="cell" /><strong role="cell">{breakdown.score.toFixed(2)}</strong></div>
        </div>
        <h4>Exploratory weight sensitivity</h4>
        <p>Small one-at-a-time weight changes assess ranking stability. They are not validated alternative formulas.</p>
        <div className="sensitivity-list">{recommendation.sensitivity_analysis.map((item) => <div key={item.scenario_id}><span>{item.label}</span><strong>{item.score.toFixed(2)} · Rank {item.rank}</strong></div>)}</div>
        <h4>Traceability statement</h4>
        <p>{recommendation.traceability}</p>
      </div>
    </details>
  </article>
}
