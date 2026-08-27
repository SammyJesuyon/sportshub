import { useEffect, useRef, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import type { Fixture, Team, TeamSchedule } from '../api/types'
import { useAuth } from '../auth/context'

const RECENT_TEAMS_KEY = 'sportshub.recent_team_searches.v1'

function storedRecentTeams() {
  try {
    const stored = JSON.parse(localStorage.getItem(RECENT_TEAMS_KEY) ?? '[]')
    if (!Array.isArray(stored)) return []
    return stored.filter((team): team is Team => Boolean(team && typeof team.id === 'string' && typeof team.name === 'string')).slice(0, 5)
  } catch {
    return []
  }
}

function TeamSearch({ followed = [], onFollow, onSelect, selectedId }: { followed?: Team[]; onFollow?: (team: Team) => Promise<void>; onSelect?: (team: Team) => Promise<void>; selectedId?: string }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<Team[]>([])
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)

  const search = async (event: FormEvent) => {
    event.preventDefault(); setLoading(true); setError(''); setMessage('')
    try { setResults(await api.searchTeams(query)) }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Team search failed.') }
    finally { setLoading(false) }
  }

  const follow = async (team: Team) => {
    if (!onFollow) return
    setError(''); setMessage('')
    try { await onFollow(team); setMessage(`${team.name} is now in your hub.`) }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Could not follow that team.') }
  }

  return <div className="panel"><form className="search-form" onSubmit={search}><label htmlFor="team-search">Team name</label><div><input id="team-search" minLength={2} required value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Try Arsenal or Barcelona" /><button className="button primary" disabled={loading}>{loading ? 'Searching...' : 'Search'}</button></div></form>{error && <div className="error-message" role="alert">{error}</div>}{message && <div className="success-message" role="status">{message}</div>}<div className="team-list">{results.map((team) => {
    const isFollowed = followed.some((item) => item.id === team.id)
    return <article className={`team-row ${selectedId === team.id ? 'selected-team-row' : ''}`} key={team.id}><div className="team-identity">{team.logo_url ? <img src={team.logo_url.replace(/^http:\/\//, 'https://')} referrerPolicy="no-referrer" alt="" /> : <span className="team-placeholder">{team.name[0]}</span>}<div><h3>{team.name}</h3><p>{team.country ?? 'International'}</p></div></div>{onSelect ? <button className="button secondary small" disabled={selectedId === team.id} onClick={() => onSelect(team)}>{selectedId === team.id ? 'Details open' : 'View details'}</button> : onFollow ? <button className="button secondary small" disabled={isFollowed} onClick={() => follow(team)}>{isFollowed ? 'Following' : 'Follow'}</button> : null}</article>
  })}{!loading && results.length === 0 && <div className="empty-state">Search the football catalog by club name.</div>}</div></div>
}

function fixtureDate(fixture: Fixture) {
  return fixture.kickoff.slice(0, 10)
}

function fixtureTime(fixture: Fixture) {
  return new Intl.DateTimeFormat(undefined, {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  }).format(new Date(fixture.kickoff))
}

function TeamFixtureSpotlight({ fixture, label }: { fixture: Fixture; label: string }) {
  const showScore = fixture.bucket !== 'scheduled'
  return <Link className={`team-fixture-card ${fixture.bucket}`} to={`/fixtures/${fixture.fixture_id}?date=${fixtureDate(fixture)}&timezone=${encodeURIComponent(fixture.timezone)}`}>
    <span>{label} · {fixture.league_name}</span>
    <strong>{fixture.home.name} <b>{showScore ? `${fixture.home.goals ?? '–'}–${fixture.away.goals ?? '–'}` : 'vs'}</b> {fixture.away.name}</strong>
    <small>{fixtureTime(fixture)} · Open fixture details →</small>
  </Link>
}

export function ExploreTeamsPage() {
  const [selected, setSelected] = useState<Team | null>(null)
  const [recentTeams, setRecentTeams] = useState<Team[]>(storedRecentTeams)
  const [schedule, setSchedule] = useState<TeamSchedule | null>(null)
  const [loadingDetails, setLoadingDetails] = useState(false)
  const [loadingSchedule, setLoadingSchedule] = useState(false)
  const [detailError, setDetailError] = useState('')
  const [scheduleError, setScheduleError] = useState('')
  const selectionRevision = useRef(0)
  const detailRail = useRef<HTMLDivElement>(null)

  const rememberTeam = (team: Team) => {
    setRecentTeams((current) => {
      const next = [team, ...current.filter((item) => item.id !== team.id)].slice(0, 5)
      localStorage.setItem(RECENT_TEAMS_KEY, JSON.stringify(next))
      return next
    })
  }

  const selectTeam = async (team: Team) => {
    const revision = ++selectionRevision.current
    const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC'
    setSelected(team)
    setSchedule(null)
    setLoadingDetails(true)
    setLoadingSchedule(true)
    setDetailError('')
    setScheduleError('')
    rememberTeam(team)
    if (typeof window.matchMedia === 'function' && window.matchMedia('(max-width: 850px)').matches) {
      window.requestAnimationFrame(() => detailRail.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }))
    }

    const [detailResult, scheduleResult] = await Promise.allSettled([
      api.teamDetail(team.id),
      api.teamSchedule(team.id, timezone),
    ])
    if (revision !== selectionRevision.current) return

    if (detailResult.status === 'fulfilled') {
      setSelected(detailResult.value)
      rememberTeam(detailResult.value)
    } else {
      setDetailError(detailResult.reason instanceof Error ? detailResult.reason.message : 'Could not load full team details.')
    }
    if (scheduleResult.status === 'fulfilled') {
      setSchedule(scheduleResult.value)
    } else {
      setScheduleError(scheduleResult.reason instanceof Error ? scheduleResult.reason.message : 'Could not load this team’s matches.')
    }
    setLoadingDetails(false)
    setLoadingSchedule(false)
  }

  const teamType = selected?.national === true ? 'National team' : selected?.national === false ? 'Club' : 'Football team'
  const yearsActive = selected?.founded ? new Date().getFullYear() - selected.founded : null
  const location = selected ? [selected.venue_address, selected.venue_city, selected.country].filter(Boolean).join(', ') : ''
  const featuredFixtures = schedule ? [
    schedule.current_fixture && { fixture: schedule.current_fixture, label: 'Live now' },
    schedule.next_fixture && { fixture: schedule.next_fixture, label: 'Next match' },
    schedule.recent_fixture && { fixture: schedule.recent_fixture, label: 'Latest result' },
  ].filter((item): item is { fixture: Fixture; label: string } => Boolean(item)) : []

  return <section className="workspace-page team-explore-page">
    <div className="page-intro"><span className="eyebrow">Football directory</span><h1>Explore a team</h1><p>Search for a particular team, select it, and get a quick useful profile. Exploring is public and never changes the teams in your hub.</p></div>
    <div className="team-discovery-grid">
      <TeamSearch onSelect={selectTeam} selectedId={selected?.id} />
      <div className="team-detail-rail" aria-live="polite" ref={detailRail}>
        {selected ? <article className={`team-profile team-profile-rail panel ${loadingDetails ? 'loading' : ''}`} aria-label={`${selected.name} team details`}>
          <header className="team-profile-header"><div className="team-profile-identity">{selected.logo_url ? <img src={selected.logo_url.replace(/^http:\/\//, 'https://')} referrerPolicy="no-referrer" alt={`${selected.name} crest`} /> : <span>{selected.name[0]}</span>}<div><span className="eyebrow">{teamType}{selected.code ? ` · ${selected.code}` : ''}</span><h2>{selected.name}</h2><p>{selected.country ?? 'International football'}{loadingDetails ? ' · Loading full details…' : ''}</p></div></div>{selected.venue_image_url && <img className="team-venue-image" src={selected.venue_image_url.replace(/^http:\/\//, 'https://')} referrerPolicy="no-referrer" alt={`${selected.venue_name ?? selected.name} venue`} />}</header>
          {detailError && <div className="error-message" role="alert">{detailError} The search profile is still shown.</div>}
          <section className="team-match-section" aria-label={`${selected.name} matches`}><span className="eyebrow">Match outlook</span><h3>What’s next</h3>{loadingSchedule ? <p>Finding the next and latest match…</p> : featuredFixtures.length ? <div className="team-fixture-list">{featuredFixtures.map((item) => <TeamFixtureSpotlight fixture={item.fixture} label={item.label} key={`${item.label}-${item.fixture.fixture_id}`} />)}</div> : <p>{scheduleError || 'No current-season matches were returned for this team.'}</p>}</section>
          <div className="team-facts" aria-label="Team facts"><div><span>Founded</span><strong>{selected.founded ?? 'Not listed'}</strong></div><div><span>Team type</span><strong>{teamType}</strong></div><div><span>Home ground</span><strong>{selected.venue_name ?? 'Not listed'}</strong></div><div><span>Capacity</span><strong>{selected.venue_capacity?.toLocaleString() ?? 'Not listed'}</strong></div><div><span>Location</span><strong>{location || 'Not listed'}</strong></div><div><span>Playing surface</span><strong>{selected.venue_surface ?? 'Not listed'}</strong></div></div>
          <div className="team-story"><span className="eyebrow">Worth knowing</span><h3>{yearsActive ? `${yearsActive} years of football identity.` : `${selected.name} at a glance.`}</h3><p>{yearsActive ? `${selected.name} was founded in ${selected.founded}.` : `${selected.name} is listed as ${teamType.toLowerCase()}${selected.country ? ` from ${selected.country}` : ''}.`} {selected.venue_capacity && selected.venue_name ? `A full ${selected.venue_name} can welcome about ${selected.venue_capacity.toLocaleString()} supporters.` : selected.venue_name ? `${selected.venue_name} is listed as the team’s home ground.` : 'Venue information has not been supplied yet.'}</p></div>
        </article> : <div className="team-profile-empty"><span aria-hidden="true">⌕</span><h2>Select a team to open its profile</h2><p>Its profile and current-season match outlook will open here without changing your hub.</p></div>}
        <aside className="panel recent-search-panel"><span className="eyebrow">Recent searches</span><h2>Pick up where you left off</h2>{recentTeams.length ? <div className="recent-team-list">{recentTeams.map((team) => <button key={team.id} onClick={() => selectTeam(team)} className={selected?.id === team.id ? 'active' : ''}>{team.logo_url ? <img src={team.logo_url.replace(/^http:\/\//, 'https://')} referrerPolicy="no-referrer" alt="" /> : <span>{team.name[0]}</span>}<span><strong>{team.name}</strong><small>{team.country ?? 'International'}</small></span></button>)}</div> : <p>Your viewed teams will appear here for faster access.</p>}</aside>
      </div>
    </div>
  </section>
}

export function MyTeamsPage() {
  const { token } = useAuth()
  const [followed, setFollowed] = useState<Team[]>([])
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [confirmingTeamId, setConfirmingTeamId] = useState<string | null>(null)
  const [removingTeamId, setRemovingTeamId] = useState<string | null>(null)

  useEffect(() => {
    if (token) api.followedTeams(token).then(setFollowed).catch(() => setError('Could not load followed teams.'))
  }, [token])

  const follow = async (team: Team) => {
    if (!token) return
    setMessage('')
    await api.followTeam(token, team.id)
    setFollowed((current) => current.some((item) => item.id === team.id) ? current : [...current, team])
    window.dispatchEvent(new Event('sportshub:alerts-changed'))
  }

  const remove = async (team: Team) => {
    if (!token) return
    setRemovingTeamId(team.id); setError(''); setMessage('')
    try {
      await api.removeTeam(token, team.id)
      setFollowed((current) => current.filter((item) => item.id !== team.id))
      setConfirmingTeamId(null)
      setMessage(`${team.name} was removed from your hub.`)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not remove that team.')
    } finally {
      setRemovingTeamId(null)
    }
  }

  return <section className="workspace-page"><div className="page-intro"><span className="eyebrow">Personalize your hub</span><h1>Choose your teams</h1><p>This authenticated space changes your account and builds your personalized match feed.</p></div>{error && <div className="error-message" role="alert">{error}</div>}{message && <div className="success-message" role="status">{message}</div>}<div className="workspace-grid"><TeamSearch followed={followed} onFollow={follow} /><aside className="panel followed-panel"><span className="eyebrow">Your hub</span><h2>Following</h2>{followed.length ? followed.map((team) => <div className="followed-team" key={team.id}><div><strong>{team.name}</strong><span>{team.country ?? 'International'}</span></div>{confirmingTeamId === team.id ? <div className="remove-confirmation"><button className="team-remove confirm" disabled={removingTeamId === team.id} onClick={() => remove(team)} aria-label={`Confirm remove ${team.name}`}>{removingTeamId === team.id ? 'Removing…' : 'Confirm'}</button><button className="team-remove cancel" disabled={removingTeamId === team.id} onClick={() => setConfirmingTeamId(null)}>Cancel</button></div> : <button className="team-remove" onClick={() => { setConfirmingTeamId(team.id); setMessage('') }} aria-label={`Remove ${team.name} from your hub`}>Remove</button>}</div>) : <p className="empty-copy">No teams followed yet. Your personalized match feed starts here.</p>}</aside></div></section>
}
