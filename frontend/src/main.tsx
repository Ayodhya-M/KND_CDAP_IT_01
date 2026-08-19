import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { api, type User } from './api'
import './styles.css'

type AuthView = 'login' | 'signup'

const stats = [
  ['Total Employees', '0', 'Employees will appear after HR upload.'],
  ['HR Records Uploaded', '0', 'No HR dataset uploaded yet.'],
  ['Economic Records Uploaded', '0', 'No economic dataset uploaded yet.'],
  ['Integration Status', 'Not started', 'Upload both datasets to begin.'],
]

function App() {
  const [user, setUser] = useState<User | null>(null)
  const [authView, setAuthView] = useState<AuthView>('login')
  const [checkingSession, setCheckingSession] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('knd_cdap_access_token')
    if (!token) {
      setCheckingSession(false)
      return
    }

    api.me(token)
      .then(setUser)
      .catch(() => localStorage.removeItem('knd_cdap_access_token'))
      .finally(() => setCheckingSession(false))
  }, [])

  const signOut = () => {
    localStorage.removeItem('knd_cdap_access_token')
    localStorage.removeItem('knd_cdap_refresh_token')
    setUser(null)
    setAuthView('login')
  }

  if (checkingSession) return <main className="loading-screen">Loading KND CDAP…</main>
  return user ? <Dashboard user={user} onSignOut={signOut} /> : <AuthPage view={authView} onViewChange={setAuthView} onLogin={setUser} />
}

function AuthPage({ view, onViewChange, onLogin }: { view: AuthView; onViewChange: (view: AuthView) => void; onLogin: (user: User) => void }) {
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const isLogin = view === 'login'

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError('')
    setMessage('')
    setSubmitting(true)
    try {
      if (!isLogin) {
        await api.register(email, password, fullName)
        setMessage('Account created. You can now sign in.')
        setPassword('')
        onViewChange('login')
        return
      }
      const session = await api.login(email, password)
      localStorage.setItem('knd_cdap_access_token', session.access_token)
      localStorage.setItem('knd_cdap_refresh_token', session.refresh_token)
      onLogin(await api.me(session.access_token))
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : 'Unable to continue. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="auth-layout">
      <section className="brand-panel">
        <p className="eyebrow">KND CDAP IT 01</p>
        <h1>Make HR data meaningful.</h1>
        <p>Connect employee records with economic indicators to understand and predict attrition.</p>
        <div className="workflow-note"><span>01</span> Upload · Clean · Map · Predict</div>
      </section>
      <section className="auth-card" aria-labelledby="auth-title">
        <p className="eyebrow">Welcome</p>
        <h2 id="auth-title">{isLogin ? 'Sign in to your workspace' : 'Create your research workspace'}</h2>
        <p className="muted">{isLogin ? 'Enter your details to continue.' : 'Start organising your HR and economic datasets.'}</p>
        <form onSubmit={submit}>
          {!isLogin && <label>Full name<input required value={fullName} onChange={(event) => setFullName(event.target.value)} placeholder="Your name" /></label>}
          <label>Email address<input required type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@example.com" /></label>
          <label>Password<input required type="password" minLength={8} value={password} onChange={(event) => setPassword(event.target.value)} placeholder="At least 8 characters" /></label>
          {error && <p className="alert error" role="alert">{error}</p>}
          {message && <p className="alert success">{message}</p>}
          <button className="primary-button" disabled={submitting}>{submitting ? 'Please wait…' : isLogin ? 'Sign in' : 'Create account'}</button>
        </form>
        <p className="switch-text">{isLogin ? 'New to KND CDAP?' : 'Already have an account?'} <button type="button" className="text-button" onClick={() => { setError(''); setMessage(''); onViewChange(isLogin ? 'signup' : 'login') }}>{isLogin ? 'Create an account' : 'Sign in'}</button></p>
      </section>
    </main>
  )
}

function Dashboard({ user, onSignOut }: { user: User; onSignOut: () => void }) {
  return <main className="dashboard-layout">
    <aside className="sidebar"><div><p className="eyebrow">KND CDAP</p><h2>Research Hub</h2></div><nav><a className="active">Dashboard</a><a>Upload HR data</a><a>Upload economic data</a><a>Data validation</a><a>Predictions</a></nav><button className="signout-button" onClick={onSignOut}>Sign out</button></aside>
    <section className="dashboard-content">
      <header><div><p className="eyebrow">Overview</p><h1>Good to see you, {user.full_name || user.email.split('@')[0]}.</h1><p className="muted">Your HR attrition analysis workspace is ready.</p></div><button className="primary-button compact">Upload dataset</button></header>
      <div className="stats-grid">{stats.map(([label, value, detail]) => <article className="stat-card" key={label}><p>{label}</p><strong>{value}</strong><small>{detail}</small></article>)}</div>
      <section className="next-step"><div><p className="eyebrow">Get started</p><h2>Upload your HR dataset</h2><p>Use a CSV or Excel file containing employee information. We will then guide you through cleaning and temporal mapping.</p></div><button className="primary-button">Upload HR dataset</button></section>
      <section className="activity"><h2>Workflow progress</h2><div className="progress-steps"><span className="current">1<br /><small>Upload</small></span><span>2<br /><small>Clean</small></span><span>3<br /><small>Map</small></span><span>4<br /><small>Predict</small></span></div></section>
    </section>
  </main>
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
