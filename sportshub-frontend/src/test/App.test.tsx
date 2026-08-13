import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from '../App'
import { AuthProvider } from '../auth/AuthContext'

function jsonResponse(body: unknown, status = 200) {
  return Promise.resolve(new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  }))
}

function renderApp(path = '/') {
  return render(<MemoryRouter initialEntries={[path]}><AuthProvider><App /></AuthProvider></MemoryRouter>)
}

afterEach(() => vi.restoreAllMocks())

describe('SportsHub web foundation', () => {
  it('renders real matchday sections and distinct team journeys', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation((input) => {
      if (String(input).endsWith('/fixtures/matchday')) return jsonResponse({
        date: '2026-08-13', timezone: 'UTC', fixtures: [
          { fixture_id: 1, kickoff: '2026-08-13T19:00:00+00:00', timezone: 'UTC', league_id: 39, league_name: 'Premier League', league_logo_url: null, status_short: '2H', status_long: 'Second Half', elapsed: 72, bucket: 'live', home: { provider_id: 42, name: 'Arsenal', logo_url: null, goals: 2 }, away: { provider_id: 49, name: 'Chelsea', logo_url: null, goals: 1 } },
        ],
      })
      return jsonResponse({}, 404)
    })
    renderApp()
    expect(screen.getByRole('heading', { name: /every score/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /create your fan profile/i })).toHaveAttribute('href', '/register')
    expect(screen.getByRole('link', { name: /explore teams/i })).toHaveAttribute('href', '/explore/teams')
    expect(await screen.findByRole('heading', { name: /live now/i })).toBeInTheDocument()
    expect(screen.getAllByText('Arsenal')).not.toHaveLength(0)
  })

  it('protects team preferences behind authentication', async () => {
    renderApp('/my/teams')
    expect(await screen.findByRole('heading', { name: /welcome back/i })).toBeInTheDocument()
  })

  it('keeps team exploration public and does not expose follow actions', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation((input) => {
      if (String(input).includes('/teams/?search=')) return jsonResponse([{ id: 'team-1', api_team_id: 42, third_party_id: '42', name: 'Arsenal', country: 'England', logo_url: null }])
      return jsonResponse({}, 404)
    })
    const user = userEvent.setup()
    renderApp('/explore/teams')
    await user.type(screen.getByLabelText(/team name/i), 'Arsenal')
    await user.click(screen.getByRole('button', { name: /^search$/i }))
    expect(await screen.findByRole('heading', { name: /explore teams/i })).toBeInTheDocument()
    expect(await screen.findByRole('link', { name: /sign in to follow/i })).toHaveAttribute('href', '/login')
    expect(screen.queryByRole('button', { name: /^follow$/i })).not.toBeInTheDocument()
  })

  it('registers a fan and navigates to team selection', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(() => jsonResponse({
      access_token: 'token-1', token_type: 'bearer',
      user: { id: 'user-1', email: 'fan@example.com', username: 'sportsfan', role: 'fan' },
    }))
    const user = userEvent.setup()
    renderApp('/register')
    await user.type(screen.getByLabelText(/email/i), 'fan@example.com')
    await user.type(screen.getByLabelText(/username/i), 'sportsfan')
    await user.type(screen.getByLabelText(/password/i), 'SecurePass123!')
    await user.click(screen.getByRole('button', { name: /create fan profile/i }))
    expect(await screen.findByRole('heading', { name: /choose your teams/i })).toBeInTheDocument()
    expect(localStorage.getItem('sportshub.access_token')).toBe('token-1')
  })

  it('searches for and follows a team with the authenticated token', async () => {
    localStorage.setItem('sportshub.access_token', 'token-1')
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation((input, init) => {
      const url = String(input)
      if (url.endsWith('/auth/me')) return jsonResponse({ id: 'user-1', email: 'fan@example.com', username: 'sportsfan', role: 'fan' })
      if (url.endsWith('/users/me/team-preferences') && (!init || init.method !== 'PUT')) return jsonResponse([])
      if (url.includes('/teams/?search=')) return jsonResponse([{ id: 'team-1', api_team_id: 42, third_party_id: '42', name: 'Arsenal', country: 'England', logo_url: null }])
      if (url.endsWith('/users/me/team-preferences') && init?.method === 'PUT') return jsonResponse({ teams: [], added_count: 1, duplicate_count: 0, not_found_ids: [] })
      return jsonResponse({}, 404)
    })
    const user = userEvent.setup()
    renderApp('/my/teams')
    await user.type(await screen.findByLabelText(/team name/i), 'Arsenal')
    await user.click(screen.getByRole('button', { name: /^search$/i }))
    await user.click(await screen.findByRole('button', { name: /^follow$/i }))
    expect(await screen.findByText(/arsenal is now in your hub/i)).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('/users/me/team-preferences'), expect.objectContaining({
      method: 'PUT',
      headers: expect.objectContaining({ Authorization: 'Bearer token-1' }),
    }))
  })

  it('rolls back a failed notification toggle', async () => {
    localStorage.setItem('sportshub.access_token', 'token-1')
    vi.spyOn(globalThis, 'fetch').mockImplementation((input, init) => {
      const url = String(input)
      if (url.endsWith('/auth/me')) return jsonResponse({ id: 'user-1', email: 'fan@example.com', username: 'sportsfan', role: 'fan' })
      if (url.endsWith('/notifications/preferences') && (!init || init.method !== 'PUT')) return jsonResponse({ enabled: true, pre_match_reminder: true, match_start: true, match_end: true })
      return jsonResponse({ detail: 'Preference update failed' }, 503)
    })
    renderApp('/alerts')
    const matchEnd = await screen.findByRole('switch', { name: /full-time result/i })
    expect(matchEnd).toHaveAttribute('aria-checked', 'true')
    fireEvent.click(matchEnd)
    expect(await screen.findByRole('alert')).toHaveTextContent(/preference update failed/i)
    await waitFor(() => expect(matchEnd).toHaveAttribute('aria-checked', 'true'))
  })
})
