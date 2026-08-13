import { useEffect, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import type { FixtureDetail } from '../api/types'

export function FixtureDetailPage() {
  const { fixtureId } = useParams()
  const [searchParams] = useSearchParams()
  const fixtureDate = searchParams.get('date') ?? new Date().toISOString().slice(0, 10)
  const [detail, setDetail] = useState<FixtureDetail | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    const parsedId = Number(fixtureId)
    if (!Number.isInteger(parsedId)) { setError('Invalid fixture.'); return }
    api.fixtureDetail(parsedId, fixtureDate).then(setDetail).catch((reason) => setError(reason instanceof Error ? reason.message : 'Could not load fixture details.'))
  }, [fixtureDate, fixtureId])

  if (error) return <section className="workspace-page narrow"><Link className="back-link" to="/">← Matchday center</Link><div className="error-message" role="alert">{error}</div></section>
  if (!detail) return <div className="page-state">Loading fixture details…</div>
  const fixture = detail.fixture
  const remaining = detail.quota.daily_remaining
  return <section className="fixture-detail-page"><div className="fixture-detail-wrap"><Link className="back-link" to="/">← Matchday center</Link><header className="fixture-detail-hero"><div><span className="eyebrow">{fixture.league_name}</span><h1>{fixture.home.name} <span>vs</span> {fixture.away.name}</h1><p>{fixture.status_long}{fixture.elapsed ? ` · ${fixture.elapsed}'` : ''}</p></div><div className="detail-score"><strong>{fixture.home.goals ?? '–'}</strong><span>:</span><strong>{fixture.away.goals ?? '–'}</strong></div></header><div className="detail-meta"><div><span>Venue</span><strong>{detail.venue_name ?? 'To be confirmed'}{detail.venue_city ? `, ${detail.venue_city}` : ''}</strong></div><div><span>Kickoff</span><strong>{new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(fixture.kickoff))}</strong></div><div><span>Referee</span><strong>{detail.referee ?? 'To be confirmed'}</strong></div></div><div className="detail-grid"><section className="panel"><span className="eyebrow">Match timeline</span><h2>Events</h2>{detail.events.length ? <div className="event-list">{detail.events.map((event, index) => <article key={`${event.elapsed}-${event.player_name}-${index}`}><time>{event.elapsed ?? '–'}'{event.extra ? `+${event.extra}` : ''}</time><div><strong>{event.event_type} · {event.detail}</strong><p>{event.player_name ?? event.team_name}{event.assist_name ? ` · Assist: ${event.assist_name}` : ''}</p></div></article>)}</div> : <p className="empty-copy">No timeline events are available yet.</p>}</section><aside className="panel detail-usage"><span className="eyebrow">Data protection</span><h2>Cached details</h2><p>Repeated visits use this stored response for {Math.ceil(detail.cache.ttl_seconds / 60)} minutes.</p><strong>{remaining === null ? 'Quota monitoring active' : `${remaining} daily API requests remaining`}</strong></aside></div></div></section>
}
