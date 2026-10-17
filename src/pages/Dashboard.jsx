import Bar from '../components/Bar'
import RiskBadge from '../components/RiskBadge'
import { factors } from '../data/mockData'

function Metric({ label, value, note, tone }) {
  return <article className={`metric ${tone || ''}`}><p>{label}</p><strong>{value}</strong><small>{note}</small></article>
}

export default function Dashboard({ employees, selected, search, setSearch, filtered, selectEmployee, openExplanation }) {
  return <>
    <section className="hero-row"><div><p className="section-label">EMPLOYEE LOOKUP</p><h2>Find a prediction</h2><div className="search"><span>⌕</span><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search by employee ID or name" /></div>{search && <div className="search-results">{filtered.map((employee) => <button key={employee.id} onClick={() => selectEmployee(employee)}>{employee.id} · {employee.name}</button>)}{!filtered.length && <span>No prototype employee found</span>}</div>}</div><div className="hero-copy"><span className="spark">✦</span><p>Focused on one decision</p><strong>Employee → prediction → explanation</strong></div></section>
    <section className="metrics"><Metric label="Risk level" value={<RiskBadge risk={selected.risk} />} note="Current assessment" /><Metric label="Turnover probability" value={`${selected.probability}%`} note="For the next 12 months" tone="coral" /><Metric label="Employee" value={selected.id} note={selected.name} /></section>
    <section className="dashboard-grid"><article className="card analysis"><div className="card-head"><div><p className="section-label">PREDICTION EXPLAINED</p><h2>Turnover risk analysis</h2></div><button className="text-button" onClick={openExplanation}>View SHAP analysis →</button></div><p className="subtle">Features with the greatest influence on this prediction</p><div className="factor-list">{factors.slice(0, 4).map(([label, value]) => <div className="factor" key={label}><span>{label}</span><Bar value={value / .31} /><b>+{value.toFixed(2)}</b></div>)}</div><div className="model-note"><span>◆</span> Contributions shown are prototype SHAP values.</div></article>
      <article className="card spotlight"><p className="section-label">HR SIGNAL</p><h2>Action-worthy insight</h2><p>Overtime and low job satisfaction are the strongest signals behind this risk assessment.</p><button onClick={openExplanation}>Understand the factors <span>→</span></button></article></section>
    <section className="card recent"><div className="card-head"><div><p className="section-label">RISK OVERVIEW</p><h2>Recent employee predictions</h2></div><button className="text-button">View all employees →</button></div><table><thead><tr><th>Employee</th><th>Department</th><th>Risk</th><th>Probability</th><th /></tr></thead><tbody>{employees.map((employee) => <tr key={employee.id}><td><strong>{employee.id}</strong><small>{employee.name}</small></td><td>{employee.department}</td><td><RiskBadge risk={employee.risk} /></td><td><div className="probability"><Bar value={employee.probability / 100} /><b>{employee.probability}%</b></div></td><td><button className="row-action" onClick={() => selectEmployee(employee)}>View →</button></td></tr>)}</tbody></table></section>
  </>
}
