import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { NotificationPreferences } from '../api/types'
import { useAuth } from '../auth/context'

const labels: Record<keyof NotificationPreferences, [string, string]> = {
  enabled: ['SportsHub alerts', 'Master switch for all match notifications.'],
  pre_match_reminder: ['Pre-match reminder', 'A reminder before followed teams kick off.'],
  match_start: ['Match started', 'Know when the action begins.'],
  match_end: ['Full-time result', 'Receive the final score when the match ends.'],
}

export function AlertsPage() {
  const { token } = useAuth()
  const [preferences, setPreferences] = useState<NotificationPreferences | null>(null)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    if (token) api.notificationPreferences(token).then(setPreferences).catch(() => setError('Could not load alert settings.'))
  }, [token])

  const toggle = async (key: keyof NotificationPreferences) => {
    if (!token || !preferences) return
    const previous = preferences
    const next = { ...preferences, [key]: !preferences[key] }
    setPreferences(next); setSaved(false); setError('')
    try { setPreferences(await api.updateNotificationPreferences(token, { [key]: next[key] })); setSaved(true) }
    catch (reason) { setPreferences(previous); setError(reason instanceof Error ? reason.message : 'Could not save settings.') }
  }

  return <section className="workspace-page narrow"><div className="page-intro"><span className="eyebrow">Stay in the moment</span><h1>Match alerts</h1><p>These settings apply globally to your account—not separately to each team.</p></div><aside className="delivery-status"><strong>Preferences are ready</strong><p>SportsHub currently saves your choices. Automatic match-event delivery and browser push registration are the next notification implementation step.</p></aside><div className="panel settings-panel">{error && <div className="error-message" role="alert">{error}</div>}{saved && <div className="success-message" role="status">Preferences saved.</div>}{!preferences ? <div className="empty-state">Loading your preferences...</div> : Object.entries(labels).map(([key, [title, description]]) => {
    const typedKey = key as keyof NotificationPreferences
    return <div className="setting-row" key={key}><div><h3>{title}</h3><p>{description}</p></div><button className={`toggle ${preferences[typedKey] ? 'on' : ''}`} role="switch" aria-checked={preferences[typedKey]} aria-label={title} onClick={() => toggle(typedKey)}><span /></button></div>
  })}</div></section>
}
