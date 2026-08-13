import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import type { AlertInbox, AlertItem } from '../api/types'
import { useAuth } from '../auth/context'

function alertIcon(kind: string) {
  if (kind === 'team_followed') return '★'
  if (kind === 'match_start') return '▶'
  if (kind === 'match_end') return 'FT'
  if (kind === 'pre_match') return '⏱'
  return 'S'
}

function alertTime(value: string) {
  const date = new Date(value.endsWith('Z') ? value : `${value}Z`)
  const today = new Date()
  return date.toDateString() === today.toDateString()
    ? new Intl.DateTimeFormat(undefined, { hour: 'numeric', minute: '2-digit' }).format(date)
    : new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }).format(date)
}

export function AlertsPage() {
  const { token } = useAuth()
  const [inbox, setInbox] = useState<AlertInbox | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (token) api.alertInbox(token).then(setInbox).catch(() => setError('Could not load your alert inbox.'))
  }, [token])

  const markRead = async (alert: AlertItem) => {
    if (!token || alert.is_read || !inbox) return
    try {
      const updated = await api.markAlertRead(token, alert.id)
      const unreadCount = Math.max(0, inbox.unread_count - 1)
      setInbox({ ...inbox, unread_count: unreadCount, items: inbox.items.map((item) => item.id === alert.id ? updated : item) })
      window.dispatchEvent(new CustomEvent('sportshub:alerts-changed', { detail: unreadCount }))
    } catch { setError('Could not update this alert.') }
  }

  const markAllRead = async () => {
    if (!token || !inbox?.unread_count) return
    try {
      await api.markAllAlertsRead(token)
      setInbox({ ...inbox, unread_count: 0, items: inbox.items.map((item) => ({ ...item, is_read: true })) })
      window.dispatchEvent(new CustomEvent('sportshub:alerts-changed', { detail: 0 }))
    } catch { setError('Could not mark alerts as read.') }
  }

  return <section className="workspace-page alert-inbox-page">
    <div className="alert-page-head">
      <div><span className="eyebrow">Your SportsHub inbox</span><h1>Alerts</h1><p>Important updates and account activity, all in one place. For now, alerts stay inside SportsHub—no push setup is required.</p></div>
      <div className="unread-summary" aria-label={`${inbox?.unread_count ?? 0} unread alerts`}><span>{inbox?.unread_count ?? 0}</span><div><strong>Unread</strong><small>{inbox?.total_items ?? 0} total alerts</small></div></div>
    </div>
    {error && <div className="error-message" role="alert">{error}</div>}
    <div className="inbox-toolbar"><h2>Inbox</h2><button className="button secondary small" disabled={!inbox?.unread_count} onClick={markAllRead}>Mark all as read</button></div>
    {!inbox ? <div className="panel empty-state">Loading your alerts...</div> : inbox.items.length === 0 ? <div className="panel inbox-empty"><span>✓</span><h2>You’re all caught up</h2><p>New SportsHub updates will appear here.</p></div> : <div className="alert-list">{inbox.items.map((alert) => {
      const content = <><span className={`alert-kind ${alert.kind}`}>{alertIcon(alert.kind)}</span><div className="alert-copy"><div><h3>{alert.title}</h3><time>{alertTime(alert.created_at)}</time></div><p>{alert.summary}</p></div>{!alert.is_read && <span className="unread-dot" aria-label="Unread" />}</>
      return alert.link_url ? <Link to={alert.link_url} className={`alert-card ${alert.is_read ? 'read' : 'unread'}`} onClick={() => markRead(alert)} key={alert.id}>{content}</Link> : <button type="button" className={`alert-card ${alert.is_read ? 'read' : 'unread'}`} onClick={() => markRead(alert)} key={alert.id}>{content}</button>
    })}</div>}
  </section>
}
