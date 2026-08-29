import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth/context'

export function AppShell() {
  const { user, token, logout } = useAuth()
  const location = useLocation()
  const [unreadCount, setUnreadCount] = useState(0)

  useEffect(() => {
    if (!token) { setUnreadCount(0); return }
    const refreshUnreadCount = () => {
      api.alertInbox(token).then((inbox) => setUnreadCount(inbox.unread_count)).catch(() => setUnreadCount(0))
    }
    const handleAlertsChanged = (event: Event) => {
      const nextCount = (event as CustomEvent<number>).detail
      if (typeof nextCount === 'number') setUnreadCount(nextCount)
      else refreshUnreadCount()
    }
    refreshUnreadCount()
    window.addEventListener('sportshub:alerts-changed', handleAlertsChanged)
    window.addEventListener('focus', refreshUnreadCount)
    return () => {
      window.removeEventListener('sportshub:alerts-changed', handleAlertsChanged)
      window.removeEventListener('focus', refreshUnreadCount)
    }
  }, [location.pathname, token])

  return <div className="app-shell">
    <header className="topbar">
      <NavLink to="/" className="brand" aria-label="SportsHub home"><span className="brand-mark" aria-hidden="true">S</span><span>SportsHub</span></NavLink>
      <nav aria-label="Primary navigation"><NavLink to="/">Home</NavLink><NavLink to="/explore/teams">Explore</NavLink>{user && <NavLink to="/my/teams">My teams</NavLink>}<NavLink to="/alerts" className="alert-nav-link" aria-label={user && unreadCount ? `Alerts, ${unreadCount} unread` : 'Alerts'}><svg className="alert-nav-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4" /></svg><span className="alert-nav-label">Alerts</span>{user && unreadCount > 0 && <span className="nav-alert-badge" aria-hidden="true">{unreadCount > 99 ? '99+' : unreadCount}</span>}</NavLink></nav>
      <div className="account-actions">{user ? <><NavLink className="user-chip" to="/profile" aria-label={`Open profile for @${user.username}`}>@{user.username}</NavLink><button className="button ghost" onClick={logout}>Sign out</button></> : <NavLink className="button primary small" to="/login">Sign in</NavLink>}</div>
    </header>
    <main><Outlet /></main>
    <footer><span>SportsHub Enterprise</span><span>One place. Every match that matters.</span></footer>
  </div>
}
