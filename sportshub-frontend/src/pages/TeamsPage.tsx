import { useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import type { Team } from '../api/types'
import { useAuth } from '../auth/context'

function TeamSearch({ followed = [], onFollow }: { followed?: Team[]; onFollow?: (team: Team) => Promise<void> }) {
  const { user } = useAuth()
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
    return <article className="team-row" key={team.id}><div className="team-identity">{team.logo_url ? <img src={team.logo_url} alt="" /> : <span className="team-placeholder">{team.name[0]}</span>}<div><h3>{team.name}</h3><p>{team.country ?? 'International'}</p></div></div>{onFollow ? <button className="button secondary small" disabled={isFollowed} onClick={() => follow(team)}>{isFollowed ? 'Following' : 'Follow'}</button> : user ? <Link className="button secondary small" to="/my/teams">Choose</Link> : <Link className="button secondary small" to="/login" state={{ from: { pathname: '/my/teams' } }}>Sign in to follow</Link>}</article>
  })}{!loading && results.length === 0 && <div className="empty-state">Search the football catalog by club name.</div>}</div></div>
}

export function ExploreTeamsPage() {
  return <section className="workspace-page"><div className="page-intro"><span className="eyebrow">Football directory</span><h1>Explore teams</h1><p>Browse verified clubs without signing in. When you want a personalized match feed, continue to My teams and choose the clubs you follow.</p></div><div className="explore-grid"><TeamSearch /><aside className="panel journey-panel"><span className="eyebrow">Public journey</span><h2>Discover first.</h2><p>Explore is for browsing. It does not change your account.</p><Link className="button primary" to="/my/teams">Choose your teams</Link></aside></div></section>
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
