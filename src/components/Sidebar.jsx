import { navigation } from '../data/mockData'

export default function Sidebar({ page, setPage }) {
  return <aside className="sidebar">
    <div className="brand"><span className="brand-mark">↑</span><span>Attrition<span className="accent">IQ</span></span></div>
    <p className="module-tag">MODULE 03 · PROTOTYPE</p>
    <nav>{navigation.map(([label, icon]) => <button key={label} className={page === label ? 'active' : ''} onClick={() => setPage(label)}><span>{icon}</span>{label}</button>)}</nav>
    <div className="side-note"><span className="pulse" />Model integration<br /><strong>Prototype mode</strong></div>
    <div className="profile"><div className="avatar">HR</div><div><strong>HR workspace</strong><small>Decision support</small></div><span>⌄</span></div>
  </aside>
}
