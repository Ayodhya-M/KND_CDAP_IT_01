import type { Module4Recommendation } from '../api'
import { formatFeatureName } from './RiskFactorsList'

function levelClass(level: string) {
  const normalized = level.toLowerCase()
  return ['low', 'medium', 'high'].includes(normalized) ? normalized : 'neutral'
}

export function RetentionActionPlan({ recommendations }: { recommendations: Module4Recommendation[] }) {
  return <section className="retention-action-plan" aria-labelledby="action-plan-heading">
    <header className="module4-section-banner">
      <div><p>Module 4 · HR planning view</p><h2 id="action-plan-heading">Retention Action Plan</h2></div>
      <span>{recommendations.length} proposed action{recommendations.length === 1 ? '' : 's'}</span>
    </header>

    <div className="action-plan-intro">
      <p>Translate the current ranked recommendations into a reviewable HR plan. Ownership, dates, and progress tracking are proposed future capabilities and are not saved.</p>
      <span>Unsaved planning preview</span>
    </div>

    {recommendations.length === 0
      ? <div className="action-plan-empty"><strong>No action plan generated</strong><p>No supported recommendation is available for the current analysis. This does not mean turnover is impossible.</p></div>
      : <div className="action-plan-table" role="table" aria-label="Retention action plan generated from current recommendations">
        <div className="action-plan-head" role="row">
          <span role="columnheader">Action and rationale</span><span role="columnheader">Related factor</span><span role="columnheader">Priority</span><span role="columnheader">Draft planning</span>
        </div>
        {recommendations.map((recommendation, index) => <article className="action-plan-row" role="row" key={recommendation.recommendation_id}>
          <div className="action-plan-action" role="cell"><span className="action-plan-rank">{index + 1}</span><div><h3>{recommendation.title}</h3><p>{recommendation.explanation}</p><strong>Suggested HR review</strong><p>{recommendation.suggested_action}</p><small>Rule: {recommendation.recommendation_id} · {recommendation.rule_version}</small></div></div>
          <div className="action-plan-factor" role="cell"><span>{recommendation.category}</span><strong>{formatFeatureName(recommendation.related_factor)}</strong></div>
          <div className="action-plan-priority" role="cell"><strong>{recommendation.priority_score.toFixed(1)}</strong><span className={`status-badge ${levelClass(recommendation.priority_level)}`}>{recommendation.priority_level}</span><small>Action ranking</small></div>
          <dl className="action-plan-draft" role="cell"><div><dt>Responsible HR person</dt><dd>Unassigned</dd></div><div><dt>Target date</dt><dd>Not scheduled</dd></div><div><dt>Action status</dt><dd>Draft · not tracked</dd></div></dl>
        </article>)}
      </div>}

    <div className="hr-workflow" aria-label="Proposed retention action workflow">
      {['Review Recommendation', 'Create Action Plan', 'Assign Responsible Person', 'Monitor Progress'].map((step, index) => <div className={index === 0 ? 'available' : 'future'} key={step}><span>{index + 1}</span><strong>{step}</strong><small>{index === 0 ? 'Available now' : 'Proposed future functionality'}</small></div>)}
    </div>

    <aside className="evaluation-workflow">
      <div><p>Future research lifecycle</p><h3>Proposed Evaluation Workflow</h3></div>
      <ol>{['Implement Action', 'Monitor Outcomes', 'Evaluate Retention Impact', 'Review Recommendations'].map((step) => <li key={step}>{step}</li>)}</ol>
      <p>No outcome tracking, completed evaluation, or intervention-effect evidence is currently recorded by this prototype.</p>
    </aside>
  </section>
}
