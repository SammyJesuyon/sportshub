import { useEffect, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import type { FixtureDetail, FixtureEvent, FixtureLineupPlayer, FixtureTeamStatistics } from '../api/types'

const preferredStatistics = [
  'Ball Possession',
  'Total Shots',
  'Shots on Goal',
  'Shots off Goal',
  'Blocked Shots',
  'Corner Kicks',
  'Offsides',
  'Fouls',
  'Yellow Cards',
  'Red Cards',
  'Goalkeeper Saves',
  'Total passes',
  'Passes accurate',
  'Passes %',
]

function statisticValue(team: FixtureTeamStatistics | undefined, name: string) {
  return team?.statistics.find((statistic) => statistic.name === name)?.value ?? '–'
}

function Statistics({ detail }: { detail: FixtureDetail }) {
  const home = detail.statistics.find((team) => team.provider_id === detail.fixture.home.provider_id) ?? detail.statistics[0]
  const away = detail.statistics.find((team) => team.provider_id === detail.fixture.away.provider_id) ?? detail.statistics[1]
  const availableNames = new Set(detail.statistics.flatMap((team) => team.statistics.map((statistic) => statistic.name)))
  const rows = [
    ...preferredStatistics.filter((name) => availableNames.has(name)),
    ...Array.from(availableNames).filter((name) => !preferredStatistics.includes(name)),
  ]

  return <section className="panel match-statistics"><div className="section-title"><div><span className="eyebrow">Team comparison</span><h2>Match statistics</h2></div></div>{rows.length ? <><div className="statistics-team-head"><strong>{detail.fixture.home.name}</strong><span>STAT</span><strong>{detail.fixture.away.name}</strong></div><div className="statistics-list">{rows.map((name) => <div className="statistic-row" key={name}><strong>{statisticValue(home, name)}</strong><span>{name}</span><strong>{statisticValue(away, name)}</strong></div>)}</div></> : <p className="empty-copy">Statistics will appear here when the match data provider publishes them.</p>}</section>
}

function PlayerList({ title, players }: { title: string; players: FixtureLineupPlayer[] }) {
  if (!players.length) return null
  return <div className="squad-list"><h4>{title}</h4>{players.map((player, index) => <div className="lineup-player" key={`${player.provider_id ?? player.name}-${index}`}><span>{player.number ?? '–'}</span><strong>{player.name}</strong><small>{player.position ?? ''}</small></div>)}</div>
}

function Lineups({ detail }: { detail: FixtureDetail }) {
  return <section className="panel lineups-panel"><div className="section-title"><div><span className="eyebrow">Teamsheets</span><h2>Lineups</h2></div></div>{detail.lineups.length ? <div className="lineup-grid">{detail.lineups.map((lineup) => <article className="team-lineup" key={`${lineup.provider_id ?? lineup.team_name}`}><header><div>{lineup.logo_url && <img src={lineup.logo_url} alt="" />}<div><h3>{lineup.team_name}</h3><p>{lineup.formation ? `Formation ${lineup.formation}` : 'Formation not confirmed'}</p></div></div>{lineup.coach_name && <span>Coach · {lineup.coach_name}</span>}</header><PlayerList title="Starting XI" players={lineup.starting_xi} /><PlayerList title="Substitutes" players={lineup.substitutes} /></article>)}</div> : <p className="empty-copy">Lineups will appear here when the teamsheets are announced.</p>}</section>
}

function eventCopy(event: FixtureEvent) {
  if (event.event_type.toLowerCase() === 'subst') {
    return {
      title: `Substitution · ${event.detail}`,
      summary: `${event.player_name ?? 'Player'} off${event.assist_name ? ` · ${event.assist_name} on` : ''}`,
    }
  }
  return {
    title: `${event.event_type} · ${event.detail}`,
    summary: `${event.player_name ?? event.team_name}${event.assist_name ? ` · Assist: ${event.assist_name}` : ''}`,
  }
}

function Timeline({ detail }: { detail: FixtureDetail }) {
  return <section className="panel timeline-panel"><div className="section-title"><div><span className="eyebrow">Minute by minute</span><h2>Match timeline</h2></div><span>{detail.events.length} events</span></div>{detail.events.length ? <div className="event-list">{detail.events.map((event, index) => { const copy = eventCopy(event); return <article key={`${event.elapsed}-${event.player_name}-${index}`}><time>{event.elapsed ?? '–'}'{event.extra ? `+${event.extra}` : ''}</time><div><strong>{copy.title}</strong><p>{copy.summary}</p><small>{event.team_name}</small></div></article> })}</div> : <p className="empty-copy">No timeline events are available yet.</p>}</section>
}

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

  return <section className="fixture-detail-page"><div className="fixture-detail-wrap"><Link className="back-link" to="/">← Matchday center</Link><header className="fixture-detail-hero"><div><span className="eyebrow">{fixture.league_name}</span><h1>{fixture.home.name} <span>vs</span> {fixture.away.name}</h1><p>{fixture.status_long}{fixture.elapsed ? ` · ${fixture.elapsed}'` : ''}</p></div><div className="detail-score"><strong>{fixture.home.goals ?? '–'}</strong><span>:</span><strong>{fixture.away.goals ?? '–'}</strong></div></header><div className="detail-meta"><div><span>Venue</span><strong>{detail.venue_name ?? 'To be confirmed'}{detail.venue_city ? `, ${detail.venue_city}` : ''}</strong></div><div><span>Kickoff</span><strong>{new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(fixture.kickoff))}</strong></div><div><span>Referee</span><strong>{detail.referee ?? 'To be confirmed'}</strong></div></div><div className="fixture-content"><Statistics detail={detail} /><Lineups detail={detail} /><Timeline detail={detail} /></div></div></section>
}
