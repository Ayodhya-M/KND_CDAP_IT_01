import RiskBadge from '../components/RiskBadge'

export default function EmployeeOverview({ employees, selectEmployee }) {
  return <section className="card overview"><div className="card-head"><div><p className="section-label">PROTOTYPE DIRECTORY</p><h2>Employee risk overview</h2></div><span className="count">{employees.length} employees</span></div><table><thead><tr><th>Employee</th><th>Department</th><th>Role</th><th>Risk</th><th>Probability</th><th /></tr></thead><tbody>{employees.map((employee) => <tr key={employee.id}><td><strong>{employee.id}</strong><small>{employee.name}</small></td><td>{employee.department}</td><td>{employee.role}</td><td><RiskBadge risk={employee.risk} /></td><td>{employee.probability}%</td><td><button className="row-action" onClick={() => selectEmployee(employee)}>Open →</button></td></tr>)}</tbody></table></section>
}
