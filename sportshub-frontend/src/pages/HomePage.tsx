import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import type { Fixture, FixtureBucket } from '../api/types'
import { useAuth } from '../auth/context'

const sections: { bucket: FixtureBucket; title: string; label: string }[] = [
  { bucket: 'live', title: 'Live now', label: 'In play' },
  { bucket: 'half_time', title: 'Half-time', label: 'HT' },
  { bucket: 'full_time', title: 'Full-time', label: 'FT' },
  { bucket: 'scheduled', title: 'Coming up', label: 'Today' },
]

function statusLabel(fixture: Fixture) {
  if (fixture.bucket === 'live') return fixture.elapsed ? `${fixture.elapsed}'` : 'LIVE'
  if (fixture.bucket === 'half_time') return 'HT'
  if (fixture.bucket === 'full_time') return 'FT'
  if (fixture.status_short !== 'NS') return fixture.status_short
  return new Intl.DateTimeFormat(undefined, { hour: 'numeric', minute: '2-digit' }).format(new Date(fixture.kickoff))
}

function FixtureCard({ fixture }: { fixture: Fixture }) {
  const showScore = fixture.bucket !== 'scheduled'
  return <article className={`match-card ${fixture.bucket}`}><div className="match-card-head"><span>{fixture.league_name}</span><strong>{statusLabel(fixture)}</strong></div><div className="match-team"><span>{fixture.home.name}</span><b>{showScore ? fixture.home.goals ?? 0 : '–'}</b></div><div className="match-team"><span>{fixture.away.name}</span><b>{showScore ? fixture.away.goals ?? 0 : '–'}</b></div></article>
}

export function HomePage() {
  const { user } = useAuth()
  const [fixtures, setFixtures] = useState<Fixture[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadMatchday = useCallback(async () => {
    setLoading(true)
    try {
      const matchday = await api.matchday()
      setFixtures(matchday.fixtures)
      setError('')
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not load matchday.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadMatchday()
  }, [loadMatchday])

  const counts = useMemo(() => Object.fromEntries(sections.map(({ bucket }) => [bucket, fixtures.filter((fixture) => fixture.bucket === bucket).length])), [fixtures])
  const lead = fixtures.find((fixture) => fixture.bucket === 'live') ?? fixtures.find((fixture) => fixture.bucket === 'half_time') ?? fixtures.find((fixture) => fixture.bucket === 'full_time') ?? fixtures[0]

  return <>
    <section className="hero-section">
      <div className="hero-copy"><span className="eyebrow">Your matchday command center</span><h1>Every score.<br /><em>One home.</em></h1><p>Follow the teams you love, stay close to live action, and discover official tickets without switching between apps.</p><div className="hero-actions"><Link className="button primary" to={user ? '/my/teams' : '/register'}>{user ? 'Choose your teams' : 'Create your fan profile'}</Link><Link className="button secondary" to="/explore/teams">Explore teams</Link></div></div>
      {lead ? <div className="score-card" aria-label="Featured match"><div className="live-label"><span /> {statusLabel(lead)}</div><p>{lead.league_name}</p><div className="score-row"><strong>{lead.home.name}</strong><span>{lead.home.goals ?? '–'}</span></div><div className="score-row"><strong>{lead.away.name}</strong><span>{lead.away.goals ?? '–'}</span></div><div className="match-pulse">Current state from API-Football · {lead.status_long}</div></div> : <div className="score-card empty-score"><span className="eyebrow">Matchday</span><h2>{loading ? 'Loading today’s games…' : 'No fixtures available yet.'}</h2><p>{error || 'Check back as today’s schedule is published.'}</p></div>}
    </section>
    <section className="matchday-section"><div className="matchday-heading"><div><span className="eyebrow">Today’s football</span><h2>Matchday center</h2><p>Live, half-time, finished, and upcoming fixtures from the football provider.</p></div><button className="button secondary small" disabled={loading} onClick={loadMatchday}>{loading ? 'Refreshing…' : 'Refresh scores'}</button></div>{error && <div className="error-message" role="alert">{error}</div>}{loading && fixtures.length === 0 ? <div className="matchday-loading">Loading today’s fixtures…</div> : sections.map((section) => {
      const matches = fixtures.filter((fixture) => fixture.bucket === section.bucket)
      return <section className="score-section" key={section.bucket}><div className="score-section-heading"><div><span className={`status-dot ${section.bucket}`} /> <h3>{section.title}</h3></div><span>{counts[section.bucket]} {section.label}</span></div>{matches.length ? <div className="match-grid">{matches.slice(0, 12).map((fixture) => <FixtureCard fixture={fixture} key={fixture.fixture_id} />)}</div> : <p className="section-empty">No {section.title.toLowerCase()} fixtures right now.</p>}</section>
    })}</section>
  </>
}
