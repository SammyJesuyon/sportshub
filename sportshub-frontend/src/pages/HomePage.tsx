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

function localDateValue(date = new Date()) {
  const offset = date.getTimezoneOffset() * 60_000
  return new Date(date.getTime() - offset).toISOString().slice(0, 10)
}

function shiftDate(date: string, days: number) {
  const value = new Date(`${date}T12:00:00`)
  value.setDate(value.getDate() + days)
  return localDateValue(value)
}

function dateHeading(date: string) {
  const today = localDateValue()
  if (date === today) return 'Today’s football'
  if (date === shiftDate(today, -1)) return 'Yesterday’s football'
  if (date === shiftDate(today, 1)) return 'Tomorrow’s football'
  return new Intl.DateTimeFormat(undefined, { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' }).format(new Date(`${date}T12:00:00`))
}

function statusLabel(fixture: Fixture) {
  if (fixture.bucket === 'live') return fixture.elapsed ? `${fixture.elapsed}'` : 'LIVE'
  if (fixture.bucket === 'half_time') return 'HT'
  if (fixture.bucket === 'full_time') return 'FT'
  if (fixture.status_short !== 'NS') return fixture.status_short
  return 'UPCOMING'
}

function localKickoffTime(fixture: Fixture) {
  return new Intl.DateTimeFormat(undefined, {
    hour: 'numeric',
    minute: '2-digit',
    timeZoneName: 'short',
  }).format(new Date(fixture.kickoff))
}

function kickoffDateInZone(fixture: Fixture, timezone: string) {
  const parts = new Intl.DateTimeFormat('en-CA', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    timeZone: timezone,
  }).formatToParts(new Date(fixture.kickoff))
  const values = Object.fromEntries(parts.map((part) => [part.type, part.value]))
  return `${values.year}-${values.month}-${values.day}`
}

function FixtureCard({ fixture, fixtureDate, timezone }: { fixture: Fixture; fixtureDate: string; timezone: string }) {
  const showScore = fixture.bucket !== 'scheduled'
  return <Link className="match-card-link" to={`/fixtures/${fixture.fixture_id}?date=${fixtureDate}&timezone=${encodeURIComponent(timezone)}`} aria-label={`View ${fixture.home.name} versus ${fixture.away.name} fixture details`}><article className={`match-card ${fixture.bucket}`}><div className="match-card-head"><span>{fixture.league_name}</span><strong>{statusLabel(fixture)}</strong></div><div className="match-kickoff">Kickoff {localKickoffTime(fixture)}</div><div className="match-team"><span>{fixture.home.name}</span><b>{showScore ? fixture.home.goals ?? 0 : '–'}</b></div><div className="match-team"><span>{fixture.away.name}</span><b>{showScore ? fixture.away.goals ?? 0 : '–'}</b></div><span className="match-detail-link">Fixture details →</span></article></Link>
}

export function HomePage() {
  const { user } = useAuth()
  const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC'
  const [selectedDate, setSelectedDate] = useState(localDateValue)
  const [activeBucket, setActiveBucket] = useState<FixtureBucket>('live')
  const [page, setPage] = useState(1)
  const [matchday, setMatchday] = useState<Matchday | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let current = true
    setLoading(true)
    api.matchday(activeBucket, page, 12, selectedDate, timezone).then((result) => {
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
  }, [activeBucket, page, selectedDate, timezone])

  const visibleFixtures = matchday?.fixtures.filter(
    (fixture) => matchday.date === selectedDate && kickoffDateInZone(fixture, matchday.timezone) === selectedDate,
  ) ?? []
  const lead = visibleFixtures[0]
  const selectBucket = (bucket: FixtureBucket) => { setActiveBucket(bucket); setPage(1) }
  const selectDate = (date: string) => { setSelectedDate(date); setPage(1); setMatchday(null) }

  return <>
    <section className="hero-section">
      <div className="hero-copy"><span className="eyebrow">Your matchday command center</span><h1>Every score.<br /><em>One home.</em></h1><p>Follow the teams you love, stay close to live action, and discover official tickets without switching between apps.</p><div className="hero-actions"><Link className="button primary" to={user ? '/my/teams' : '/register'}>{user ? 'Choose your teams' : 'Create your fan profile'}</Link><Link className="button secondary" to="/explore/teams">Explore teams</Link></div></div>
      {lead ? <div className="score-card" aria-label="Featured match"><div className="live-label"><span /> {statusLabel(lead)}</div><p>{lead.league_name} · {localKickoffTime(lead)} local kickoff</p><div className="score-row"><strong>{lead.home.name}</strong><span>{lead.home.goals ?? '–'}</span></div><div className="score-row"><strong>{lead.away.name}</strong><span>{lead.away.goals ?? '–'}</span></div><Link className="match-pulse" to={`/fixtures/${lead.fixture_id}?date=${selectedDate}&timezone=${encodeURIComponent(timezone)}`}>Open fixture details · {lead.status_long}</Link></div> : <div className="score-card empty-score"><span className="eyebrow">Matchday</span><h2>{loading ? 'Loading games…' : 'No fixtures available yet.'}</h2><p>{error || 'Choose another date to browse more matches.'}</p></div>}
    </section>
    <section className="matchday-section"><div className="matchday-heading"><div><span className="eyebrow">{dateHeading(selectedDate)}</span><h2>Matchday center</h2><p>Kickoff times are shown in your local timezone: {timezone.replaceAll('_', ' ')}.</p></div><div className="date-navigation" aria-label="Choose match date"><button className="date-step" aria-label="Previous day" onClick={() => selectDate(shiftDate(selectedDate, -1))}>←</button><label><span>Match date</span><input type="date" value={selectedDate} onChange={(event) => selectDate(event.target.value)} /></label><button className="date-step" aria-label="Next day" onClick={() => selectDate(shiftDate(selectedDate, 1))}>→</button><button className="button secondary small" disabled={selectedDate === localDateValue()} onClick={() => selectDate(localDateValue())}>Today</button></div></div><div className="match-tabs" role="tablist" aria-label="Fixture status">{sections.map((section) => <button role="tab" aria-selected={activeBucket === section.bucket} className={activeBucket === section.bucket ? 'active' : ''} key={section.bucket} onClick={() => selectBucket(section.bucket)}>{section.shortLabel}<span>{matchday?.counts[section.bucket] ?? 0}</span></button>)}</div>{error && <div className="error-message" role="alert">{error}</div>}{loading && !matchday ? <div className="matchday-loading">Loading fixtures…</div> : <section className="score-section"><div className="score-section-heading"><div><span className={`status-dot ${activeBucket}`} /><h3>{sections.find((section) => section.bucket === activeBucket)?.title}</h3></div><span>{matchday?.total_items ?? 0} matches</span></div>{visibleFixtures.length ? <div className="match-grid">{visibleFixtures.map((fixture) => <FixtureCard fixture={fixture} fixtureDate={selectedDate} timezone={timezone} key={fixture.fixture_id} />)}</div> : <p className="section-empty">No fixtures in this section for {dateHeading(selectedDate).toLowerCase()}.</p>}<div className="pagination" aria-label="Fixture pagination"><button className="button secondary small" disabled={loading || page <= 1} onClick={() => setPage((current) => current - 1)}>Previous</button><span>Page {matchday?.page ?? page} of {matchday?.total_pages ?? 1}</span><button className="button secondary small" disabled={loading || !matchday || page >= matchday.total_pages} onClick={() => setPage((current) => current + 1)}>Next</button></div></section>}<aside className="more-sports-banner"><span className="more-sports-mark" aria-hidden="true">+</span><div><span className="eyebrow">Football is only the beginning</span><h2>More sports are coming soon.</h2><p>SportsHub starts with football while we build the same focused matchday experience for more sports.</p></div></aside></section>
  </>
}
