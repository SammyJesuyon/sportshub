import { useState, type FormEvent } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/context'

export function AuthPage({ mode }: { mode: 'login' | 'register' }) {
  const { token, login, register } = useAuth()
  const [email, setEmail] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()
  if (token) return <Navigate to={mode === 'register' ? '/profile' : '/my/teams'} replace />

  const submit = async (event: FormEvent) => {
    event.preventDefault(); setSubmitting(true); setError('')
    try {
      if (mode === 'register') await register(email, username, password)
      else await login(email, password)
      const destination = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname
      navigate(destination ?? (mode === 'register' ? '/profile' : '/my/teams'), { replace: true })
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Unable to continue.') }
    finally { setSubmitting(false) }
  }

  const registering = mode === 'register'
  return <section className="auth-layout"><div className="auth-message"><span className="eyebrow">Welcome to SportsHub</span><h1>{registering ? 'Build your matchday.' : 'Welcome back.'}</h1><p>Your followed teams and in-app alert inbox stay attached to your secure fan account.</p></div><form className="auth-card" onSubmit={submit}><h2>{registering ? 'Create account' : 'Sign in'}</h2>{error && <div className="error-message" role="alert">{error}</div>}<label>Email<input required type="email" value={email} onChange={(e) => setEmail(e.target.value)} /></label>{registering && <label>Username<input required minLength={3} value={username} onChange={(e) => setUsername(e.target.value)} /></label>}<label>Password<input required minLength={8} type="password" value={password} onChange={(e) => setPassword(e.target.value)} /></label><button className="button primary full" disabled={submitting}>{submitting ? 'Working...' : registering ? 'Create fan profile' : 'Sign in'}</button><p className="form-switch">{registering ? 'Already have an account?' : 'New to SportsHub?'} <Link to={registering ? '/login' : '/register'}>{registering ? 'Sign in' : 'Create one'}</Link></p></form></section>
}
