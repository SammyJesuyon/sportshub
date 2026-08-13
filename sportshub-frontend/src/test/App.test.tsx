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
  it('renders locale-aware matchday navigation and distinct team journeys', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation((input) => {
      if (String(input).includes('/fixtures/matchday?')) return jsonResponse({
        date: '2026-08-13', timezone: 'UTC', bucket: 'live', page: 1, page_size: 12, total_items: 1, total_pages: 1,
        counts: { live: 1, half_time: 0, full_time: 0, scheduled: 0 },
        fixtures: [
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
    expect(screen.queryByText(/api allowance|cache hit|daily api requests/i)).not.toBeInTheDocument()
    expect(screen.getByText(/page 1 of 1/i)).toBeInTheDocument()
    expect((screen.getByLabelText('Match date', { exact: true }) as HTMLInputElement).value).toMatch(/^\d{4}-\d{2}-\d{2}$/)
    expect(screen.getByRole('button', { name: /previous day/i })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /more sports are coming soon/i })).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledWith(expect.stringMatching(/date=\d{4}-\d{2}-\d{2}.*timezone=/), expect.any(Object))
    fireEvent.click(screen.getByRole('button', { name: /previous day/i }))
    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('date=2026-08-12'), expect.any(Object)))
  })

  it('opens complete fixture details without exposing provider operations', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation((input) => {
      if (String(input).includes('/fixtures/1?date=')) return jsonResponse({
        fixture: { fixture_id: 1, kickoff: '2026-08-13T19:00:00+00:00', timezone: 'UTC', league_id: 39, league_name: 'Premier League', league_logo_url: null, status_short: 'FT', status_long: 'Match Finished', elapsed: 90, bucket: 'full_time', home: { provider_id: 42, name: 'Arsenal', logo_url: null, goals: 2 }, away: { provider_id: 49, name: 'Chelsea', logo_url: null, goals: 1 } },
        referee: 'A. Referee', venue_name: 'Emirates Stadium', venue_city: 'London', halftime_home: 1, halftime_away: 0, fulltime_home: 2, fulltime_away: 1, extratime_home: null, extratime_away: null, penalty_home: null, penalty_away: null,
        events: [{ elapsed: 72, extra: null, team_name: 'Arsenal', player_name: 'A. Player', assist_name: null, event_type: 'Goal', detail: 'Normal Goal' }],
        statistics: [
          { provider_id: 42, team_name: 'Arsenal', logo_url: null, statistics: [{ name: 'Ball Possession', value: '58%' }, { name: 'Shots on Goal', value: '7' }] },
          { provider_id: 49, team_name: 'Chelsea', logo_url: null, statistics: [{ name: 'Ball Possession', value: '42%' }, { name: 'Shots on Goal', value: '3' }] },
        ],
        lineups: [{ provider_id: 42, team_name: 'Arsenal', logo_url: null, formation: '4-3-3', coach_name: 'M. Coach', starting_xi: [{ provider_id: 1, name: 'A. Keeper', number: 1, position: 'G', grid: '1:1' }], substitutes: [{ provider_id: 2, name: 'A. Substitute', number: 12, position: 'D', grid: null }] }],
      })
      return jsonResponse({}, 404)
    })
    renderApp('/fixtures/1?date=2026-08-13')
    expect(await screen.findByRole('heading', { name: /arsenal vs chelsea/i })).toBeInTheDocument()
    expect(screen.getByText(/emirates stadium/i)).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /overview/i })).toHaveAttribute('aria-selected', 'true')
    expect(screen.getByRole('heading', { name: /^overview$/i })).toBeInTheDocument()
    await userEvent.click(screen.getByRole('tab', { name: /statistics/i }))
    expect(screen.getByRole('heading', { name: /match statistics/i })).toBeInTheDocument()
    expect(screen.getByText(/ball possession/i)).toBeInTheDocument()
    expect(screen.getByText('58%')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('tab', { name: /^lineups$/i }))
    expect(screen.getByRole('heading', { name: /lineups/i })).toBeInTheDocument()
    expect(screen.getByText(/a\. keeper/i)).toBeInTheDocument()
    await userEvent.click(screen.getByRole('tab', { name: /timeline/i }))
    expect(screen.getByRole('heading', { name: /match timeline/i })).toBeInTheDocument()
    expect(screen.getByText(/normal goal/i)).toBeInTheDocument()
    await userEvent.click(screen.getByRole('tab', { name: /chat/i }))
    expect(screen.getByRole('heading', { name: /match chat is coming soon/i })).toBeInTheDocument()
    expect(screen.queryByText(/api allowance|cache hit|daily api requests/i)).not.toBeInTheDocument()
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

  it('shows persisted alert summaries and keeps the red unread count in sync', async () => {
    localStorage.setItem('sportshub.access_token', 'token-1')
    vi.spyOn(globalThis, 'fetch').mockImplementation((input, init) => {
      const url = String(input)
      if (url.endsWith('/auth/me')) return jsonResponse({ id: 'user-1', email: 'fan@example.com', username: 'sportsfan', role: 'fan' })
      if (url.endsWith('/notifications/inbox') && (!init || init.method !== 'PUT')) return jsonResponse({
        unread_count: 2,
        total_items: 2,
        items: [
          { id: 'alert-2', kind: 'team_followed', title: 'Arsenal added to your hub', summary: 'You are now following Arsenal.', link_url: '/my/teams', is_read: false, created_at: '2026-08-13T16:30:00' },
          { id: 'alert-1', kind: 'welcome', title: 'Welcome to SportsHub', summary: 'Your fan profile is ready.', link_url: null, is_read: false, created_at: '2026-08-13T15:30:00' },
        ],
      })
      if (url.endsWith('/notifications/inbox/read-all') && init?.method === 'PUT') return jsonResponse({ updated_count: 2 })
      return jsonResponse({}, 404)
    })
    renderApp('/alerts')
    expect(await screen.findByText(/you are now following arsenal/i)).toBeInTheDocument()
    expect(screen.getByText(/your fan profile is ready/i)).toBeInTheDocument()
    expect(screen.getByLabelText('2 unread alerts')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /alerts, 2 unread/i })).toHaveTextContent('2')
    await userEvent.click(screen.getByRole('button', { name: /mark all as read/i }))
    await waitFor(() => expect(screen.getByLabelText('0 unread alerts')).toBeInTheDocument())
    expect(screen.getByRole('link', { name: /^alerts$/i })).not.toHaveTextContent('2')
    expect(screen.queryByLabelText('Unread')).not.toBeInTheDocument()
  })
})
