import { Link } from 'react-router-dom'
import { useAuth } from '../auth/context'

const upcoming = [
  { teams: 'Arsenal vs Chelsea', league: 'Premier League', time: 'Saturday · 11:30 AM' },
  { teams: 'Barcelona vs Valencia', league: 'La Liga', time: 'Sunday · 2:00 PM' },
  { teams: 'Liverpool vs Man City', league: 'Premier League', time: 'Sunday · 3:30 PM' },
]

export function HomePage() {
  const { user } = useAuth()
  return <>
    <section className="hero-section">
      <div className="hero-copy"><span className="eyebrow">Your matchday command center</span><h1>Every score.<br /><em>One home.</em></h1><p>Follow the teams you love, stay close to live action, and discover official tickets without switching between apps.</p><div className="hero-actions"><Link className="button primary" to={user ? '/teams' : '/register'}>{user ? 'Choose your teams' : 'Create your fan profile'}</Link><Link className="button secondary" to="/teams">Explore teams</Link></div></div>
      <div className="score-card" aria-label="Example live match card"><div className="live-label"><span /> Live · 72'</div><p>Premier League</p><div className="score-row"><strong>Arsenal</strong><span>2</span></div><div className="score-row"><strong>Chelsea</strong><span>1</span></div><div className="match-pulse">Live updates arrive here when the SSE slice lands.</div></div>
    </section>
    <section className="content-section"><div className="section-heading"><div><span className="eyebrow">On the horizon</span><h2>Upcoming fixtures</h2></div><span className="section-note">Sample data until fixture ingestion is connected</span></div><div className="fixture-grid">{upcoming.map((match) => <article className="fixture-card" key={match.teams}><span>{match.league}</span><h3>{match.teams}</h3><p>{match.time}</p></article>)}</div></section>
  </>
}
