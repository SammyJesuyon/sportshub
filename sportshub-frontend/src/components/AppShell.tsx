import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../auth/context'

export function AppShell() {
  const { user, logout } = useAuth()
  return <div className="app-shell">
    <header className="topbar">
      <NavLink to="/" className="brand" aria-label="SportsHub home"><span className="brand-mark" aria-hidden="true">S</span><span>SportsHub</span></NavLink>
      <nav aria-label="Primary navigation"><NavLink to="/">Home</NavLink><NavLink to="/teams">Teams</NavLink><NavLink to="/alerts">Alerts</NavLink></nav>
      <div className="account-actions">{user ? <><span className="user-chip">@{user.username}</span><button className="button ghost" onClick={logout}>Sign out</button></> : <NavLink className="button primary small" to="/login">Sign in</NavLink>}</div>
    </header>
    <main><Outlet /></main>
    <footer><span>SportsHub Enterprise</span><span>One place. Every match that matters.</span></footer>
  </div>
}
