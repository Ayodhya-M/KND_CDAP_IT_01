export default function AppHeader({ page }) {
  const title = page === 'Employee details' ? 'Employee prediction' : page

  return <>
    <header><div><p className="eyebrow">EMPLOYEE TURNOVER INTELLIGENCE</p><h1>{title}</h1></div><div className="external"><span>Economic stress index</span><strong>Received from Module 2</strong><b>↗</b></div></header>
    <div className="prototype"><span>◉</span> Prototype data displayed — ML model and EESI integrations are pending.</div>
  </>
}
