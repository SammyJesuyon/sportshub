import { useEffect, useState, type FormEvent } from 'react'
import { api } from '../api/client'
import type { Team } from '../api/types'
import { useAuth } from '../auth/context'

export function TeamsPage() {
  const { token } = useAuth()
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<Team[]>([])
  const [followed, setFollowed] = useState<Team[]>([])
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (token) api.followedTeams(token).then(setFollowed).catch(() => setError('Could not load followed teams.'))
  }, [token])

  const search = async (event: FormEvent) => {
    event.preventDefault(); setLoading(true); setError(''); setMessage('')
    try { setResults(await api.searchTeams(query)) }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Team search failed.') }
    finally { setLoading(false) }
  }

  const follow = async (team: Team) => {
    if (!token) return
    setError(''); setMessage('')
    try {
      const result = await api.followTeam(token, team.id)
      setFollowed((current) => current.some((item) => item.id === team.id) ? current : [...current, team])
      setMessage(result.added_count ? `${team.name} is now in your hub.` : `${team.name} was already followed.`)
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Could not follow that team.') }
  }

  return <section className="workspace-page"><div className="page-intro"><span className="eyebrow">Personalize your hub</span><h1>Choose your teams</h1><p>Search the verified sports provider, then add teams to your account.</p></div><div className="workspace-grid"><div className="panel"><form className="search-form" onSubmit={search}><label htmlFor="team-search">Team name</label><div><input id="team-search" minLength={2} required value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Try Arsenal or Barcelona" /><button className="button primary" disabled={loading}>{loading ? 'Searching...' : 'Search'}</button></div></form>{error && <div className="error-message" role="alert">{error}</div>}{message && <div className="success-message" role="status">{message}</div>}<div className="team-list">{results.map((team) => {
    const isFollowed = followed.some((item) => item.id === team.id)
    return <article className="team-row" key={team.id}><div className="team-identity">{team.logo_url ? <img src={team.logo_url} alt="" /> : <span className="team-placeholder">{team.name[0]}</span>}<div><h3>{team.name}</h3><p>{team.country ?? 'International'}</p></div></div><button className="button secondary small" disabled={isFollowed} onClick={() => follow(team)}>{isFollowed ? 'Following' : 'Follow'}</button></article>
  })}{!loading && results.length === 0 && <div className="empty-state">Search for a team to begin.</div>}</div></div><aside className="panel followed-panel"><span className="eyebrow">Your hub</span><h2>Following</h2>{followed.length ? followed.map((team) => <div className="followed-team" key={team.id}><strong>{team.name}</strong><span>{team.country}</span></div>) : <p className="empty-copy">No teams followed yet. Your personalized match feed starts here.</p>}</aside></div></section>
}
