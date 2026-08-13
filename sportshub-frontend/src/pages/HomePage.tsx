import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import type { Fixture, FixtureBucket, Matchday } from '../api/types'
import { useAuth } from '../auth/context'

const sections: { bucket: FixtureBucket; title: string; shortLabel: string }[] = [
  { bucket: 'live', title: 'Live now', shortLabel: 'Live' },
  { bucket: 'half_time', title: 'Half-time', shortLabel: 'HT' },
  { bucket: 'full_time', title: 'Full-time', shortLabel: 'FT' },
  { bucket: 'scheduled', title: 'Coming up', shortLabel: 'Upcoming' },
]

function statusLabel(fixture: Fixture) {
  if (fixture.bucket === 'live') return fixture.elapsed ? `${fixture.elapsed}'` : 'LIVE'
  if (fixture.bucket === 'half_time') return 'HT'
  if (fixture.bucket === 'full_time') return 'FT'
  if (fixture.status_short !== 'NS') return fixture.status_short
  return new Intl.DateTimeFormat(undefined, { hour: 'numeric', minute: '2-digit' }).format(new Date(fixture.kickoff))
}

function FixtureCard({ fixture, fixtureDate }: { fixture: Fixture; fixtureDate: string }) {
  const showScore = fixture.bucket !== 'scheduled'
  return <Link className="match-card-link" to={`/fixtures/${fixture.fixture_id}?date=${fixtureDate}`} aria-label={`View ${fixture.home.name} versus ${fixture.away.name} fixture details`}><article className={`match-card ${fixture.bucket}`}><div className="match-card-head"><span>{fixture.league_name}</span><strong>{statusLabel(fixture)}</strong></div><div className="match-team"><span>{fixture.home.name}</span><b>{showScore ? fixture.home.goals ?? 0 : '–'}</b></div><div className="match-team"><span>{fixture.away.name}</span><b>{showScore ? fixture.away.goals ?? 0 : '–'}</b></div><span className="match-detail-link">Fixture details →</span></article></Link>
}

function QuotaAndCache({ matchday }: { matchday: Matchday }) {
  const remaining = matchday.quota.daily_remaining
  const limit = matchday.quota.daily_limit
  const refreshIn = Math.max(0, matchday.cache.ttl_seconds - matchday.cache.age_seconds)
  return <aside className="provider-health" aria-label="Football data usage"><div><span>API allowance</span><strong>{remaining === null || limit === null ? 'Monitoring…' : `${remaining} / ${limit} remaining`}</strong></div><div><span>Cached snapshot</span><strong>{matchday.cache.hit ? 'Cache hit' : 'Fresh provider data'} · refresh eligible in {Math.ceil(refreshIn / 60)}m</strong></div></aside>
}

export function HomePage() {
  const { user } = useAuth()
  const [activeBucket, setActiveBucket] = useState<FixtureBucket>('live')
  const [page, setPage] = useState(1)
  const [matchday, setMatchday] = useState<Matchday | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let current = true
    setLoading(true)
    api.matchday(activeBucket, page).then((result) => {
      if (!current) return
      setMatchday(result)
      setError('')
      if (result.total_items === 0) {
        const firstAvailable = sections.find((section) => result.counts[section.bucket] > 0)
        if (firstAvailable && firstAvailable.bucket !== activeBucket) {
          setActiveBucket(firstAvailable.bucket)
          setPage(1)
        }
      }
    }).catch((reason) => current && setError(reason instanceof Error ? reason.message : 'Could not load matchday.')).finally(() => current && setLoading(false))
    return () => { current = false }
  }, [activeBucket, page])

  const lead = matchday?.fixtures[0]
  const selectBucket = (bucket: FixtureBucket) => { setActiveBucket(bucket); setPage(1) }

  return <>
    <section className="hero-section">
      <div className="hero-copy"><span className="eyebrow">Your matchday command center</span><h1>Every score.<br /><em>One home.</em></h1><p>Follow the teams you love, stay close to live action, and discover official tickets without switching between apps.</p><div className="hero-actions"><Link className="button primary" to={user ? '/my/teams' : '/register'}>{user ? 'Choose your teams' : 'Create your fan profile'}</Link><Link className="button secondary" to="/explore/teams">Explore teams</Link></div></div>
      {lead ? <div className="score-card" aria-label="Featured match"><div className="live-label"><span /> {statusLabel(lead)}</div><p>{lead.league_name}</p><div className="score-row"><strong>{lead.home.name}</strong><span>{lead.home.goals ?? '–'}</span></div><div className="score-row"><strong>{lead.away.name}</strong><span>{lead.away.goals ?? '–'}</span></div><Link className="match-pulse" to={`/fixtures/${lead.fixture_id}?date=${matchday.date}`}>Open fixture details · {lead.status_long}</Link></div> : <div className="score-card empty-score"><span className="eyebrow">Matchday</span><h2>{loading ? 'Loading today’s games…' : 'No fixtures available yet.'}</h2><p>{error || 'Check back as today’s schedule is published.'}</p></div>}
    </section>
    <section className="matchday-section"><div className="matchday-heading"><div><span className="eyebrow">Today’s football</span><h2>Matchday center</h2><p>Paginated from one cached provider snapshot—changing pages does not spend another API request.</p></div></div>{matchday && <QuotaAndCache matchday={matchday} />}<div className="match-tabs" role="tablist" aria-label="Fixture status">{sections.map((section) => <button role="tab" aria-selected={activeBucket === section.bucket} className={activeBucket === section.bucket ? 'active' : ''} key={section.bucket} onClick={() => selectBucket(section.bucket)}>{section.shortLabel}<span>{matchday?.counts[section.bucket] ?? 0}</span></button>)}</div>{error && <div className="error-message" role="alert">{error}</div>}{loading && !matchday ? <div className="matchday-loading">Loading today’s fixtures…</div> : <section className="score-section"><div className="score-section-heading"><div><span className={`status-dot ${activeBucket}`} /><h3>{sections.find((section) => section.bucket === activeBucket)?.title}</h3></div><span>{matchday?.total_items ?? 0} matches</span></div>{matchday?.fixtures.length ? <div className="match-grid">{matchday.fixtures.map((fixture) => <FixtureCard fixture={fixture} fixtureDate={matchday.date} key={fixture.fixture_id} />)}</div> : <p className="section-empty">No fixtures in this section right now.</p>}<div className="pagination" aria-label="Fixture pagination"><button className="button secondary small" disabled={loading || page <= 1} onClick={() => setPage((current) => current - 1)}>Previous</button><span>Page {matchday?.page ?? page} of {matchday?.total_pages ?? 1}</span><button className="button secondary small" disabled={loading || !matchday || page >= matchday.total_pages} onClick={() => setPage((current) => current + 1)}>Next</button></div></section>}</section>
  </>
}
