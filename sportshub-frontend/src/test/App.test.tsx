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

afterEach(() => {
  vi.restoreAllMocks()
  localStorage.clear()
})

describe('SportsHub web foundation', () => {
  it('renders locale-aware matchday navigation and distinct team journeys', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation((input) => {
      if (String(input).includes('/fixtures/matchday?')) {
        const requestUrl = new URL(String(input))
        const requestedDate = requestUrl.searchParams.get('date')!
        const requestedTimezone = requestUrl.searchParams.get('timezone')!
        return jsonResponse({
        date: requestedDate, timezone: requestedTimezone, bucket: 'live', page: 1, page_size: 12, total_items: 2, total_pages: 1,
        counts: { live: 1, half_time: 0, full_time: 0, scheduled: 0 },
        fixtures: [
          { fixture_id: 1, kickoff: `${requestedDate}T14:00:00-05:00`, timezone: requestedTimezone, league_id: 39, league_name: 'Premier League', league_logo_url: null, status_short: '2H', status_long: 'Second Half', elapsed: 72, bucket: 'live', home: { provider_id: 42, name: 'Arsenal', logo_url: null, goals: 2 }, away: { provider_id: 49, name: 'Chelsea', logo_url: null, goals: 1 } },
          { fixture_id: 2, kickoff: '2026-08-12T14:00:00-05:00', timezone: requestedTimezone, league_id: 39, league_name: 'Premier League', league_logo_url: null, status_short: 'FT', status_long: 'Match Finished', elapsed: 90, bucket: 'full_time', home: { provider_id: 40, name: 'Liverpool', logo_url: null, goals: 1 }, away: { provider_id: 50, name: 'Manchester City', logo_url: null, goals: 1 } },
        ],
      })
      }
      return jsonResponse({}, 404)
    })
    renderApp()
    expect(screen.getByRole('heading', { name: /every score/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /create your fan profile/i })).toHaveAttribute('href', '/register')
    expect(screen.getByRole('link', { name: /explore teams/i })).toHaveAttribute('href', '/explore/teams')
    expect(await screen.findByRole('heading', { name: /live now/i })).toBeInTheDocument()
    expect(screen.getAllByText('Arsenal')).not.toHaveLength(0)
    expect(screen.queryByText('Liverpool')).not.toBeInTheDocument()
    expect(screen.getAllByText(/kickoff/i)).not.toHaveLength(0)
    expect(screen.queryByText(/api allowance|cache hit|daily api requests/i)).not.toBeInTheDocument()
    expect(screen.getByText(/page 1 of 1/i)).toBeInTheDocument()
    const matchDate = (screen.getByLabelText('Match date', { exact: true }) as HTMLInputElement).value
    expect(matchDate).toMatch(/^\d{4}-\d{2}-\d{2}$/)
    expect(screen.getByRole('button', { name: /previous day/i })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /more sports are coming soon/i })).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledWith(expect.stringMatching(/date=\d{4}-\d{2}-\d{2}.*timezone=/), expect.any(Object))
    const previousDate = new Date(`${matchDate}T12:00:00`)
    previousDate.setDate(previousDate.getDate() - 1)
    const previousDateValue = previousDate.toISOString().slice(0, 10)
    fireEvent.click(screen.getByRole('button', { name: /previous day/i }))
    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining(`date=${previousDateValue}`), expect.any(Object)))
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

  it('keeps team exploration read-only and opens useful team details', async () => {
    localStorage.removeItem('sportshub.recent_team_searches.v1')
    vi.spyOn(globalThis, 'fetch').mockImplementation((input) => {
      const url = String(input)
      if (url.includes('/teams/?search=')) return jsonResponse([{ id: 'team-1', api_team_id: 42, third_party_id: '42', name: 'Arsenal', country: 'England', logo_url: null }])
      if (url.includes('/teams/team-1/schedule')) return jsonResponse({
        current_fixture: null,
        next_fixture: { fixture_id: 9001, kickoff: '2026-08-29T15:00:00-05:00', timezone: 'America/Chicago', league_id: 39, league_name: 'Premier League', league_logo_url: null, status_short: 'NS', status_long: 'Not Started', elapsed: null, bucket: 'scheduled', home: { provider_id: 42, name: 'Arsenal', logo_url: null, goals: null }, away: { provider_id: 49, name: 'Chelsea', logo_url: null, goals: null } },
        recent_fixture: null,
      })
      if (url.endsWith('/teams/team-1')) return jsonResponse({ id: 'team-1', api_team_id: 42, third_party_id: '42', name: 'Arsenal', country: 'England', logo_url: null, code: 'ARS', founded: 1886, national: false, venue_name: 'Emirates Stadium', venue_address: 'Hornsey Road', venue_city: 'London', venue_capacity: 60260, venue_surface: 'grass', venue_image_url: null })
      return jsonResponse({}, 404)
    })
    const user = userEvent.setup()
    renderApp('/explore/teams')
    await user.type(screen.getByLabelText(/team name/i), 'Arsenal')
    await user.click(screen.getByRole('button', { name: /^search$/i }))
    expect(await screen.findByRole('heading', { name: /explore a team/i })).toBeInTheDocument()
    await user.click(await screen.findByRole('button', { name: /view details/i }))
    expect(await screen.findAllByText(/emirates stadium/i)).not.toHaveLength(0)
    expect(screen.getByText('60,260')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /140 years of football identity/i })).toBeInTheDocument()
    expect(await screen.findByRole('link', { name: /arsenal.*vs.*chelsea/i })).toBeInTheDocument()
    expect(screen.getByText(/next match.*premier league/i)).toBeInTheDocument()
    expect(screen.getByText(/pick up where you left off/i)).toBeInTheDocument()
    expect(localStorage.getItem('sportshub.recent_team_searches.v1')).toContain('Arsenal')
    expect(screen.queryByRole('link', { name: /sign in to follow/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /^follow$/i })).not.toBeInTheDocument()
  })

  it('registers a fan and opens email verification status', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(() => jsonResponse({
      access_token: 'token-1', token_type: 'bearer',
      user: { id: 'user-1', email: 'fan@example.com', pending_email: null, email_verified: false, username: 'sportsfan', role: 'fan' },
    }))
    const user = userEvent.setup()
    renderApp('/register')
    await user.type(screen.getByLabelText(/email/i), 'fan@example.com')
    await user.type(screen.getByLabelText(/username/i), 'sportsfan')
    await user.type(screen.getByLabelText(/password/i), 'SecurePass123!')
    await user.click(screen.getByRole('button', { name: /create fan profile/i }))
    expect(await screen.findByRole('heading', { name: /your profile/i })).toBeInTheDocument()
    expect(screen.getByText(/email verification required/i)).toBeInTheDocument()
    expect(localStorage.getItem('sportshub.access_token')).toBe('token-1')
  })

  it('opens the clickable username and manages the user profile', async () => {
    localStorage.setItem('sportshub.access_token', 'token-1')
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation((input, init) => {
      const url = String(input)
      if (url.endsWith('/auth/me')) return jsonResponse({ id: 'user-1', email: 'fan@example.com', pending_email: null, email_verified: true, username: 'sportsfan', role: 'fan' })
      if (url.endsWith('/notifications/inbox')) return jsonResponse({ unread_count: 0, total_items: 0, items: [] })
      if (url.includes('/fixtures/matchday?')) return jsonResponse({
        date: '2026-08-28', timezone: 'America/Chicago', bucket: 'live', page: 1, page_size: 12, total_items: 0, total_pages: 0,
        counts: { live: 0, half_time: 0, full_time: 0, scheduled: 0 }, fixtures: [],
      })
      if (url.endsWith('/users/me') && init?.method === 'PATCH') return jsonResponse({ id: 'user-1', email: 'fan@example.com', pending_email: 'updated@example.com', email_verified: true, username: 'updated_fan', role: 'fan' })
      if (url.endsWith('/users/me/email-verification') && init?.method === 'POST') return jsonResponse({ message: 'Verification email sent' }, 202)
      if (url.endsWith('/users/me/password') && init?.method === 'PUT') return Promise.resolve(new Response(null, { status: 204 }))
      if (url.endsWith('/users/me') && init?.method === 'DELETE') return Promise.resolve(new Response(null, { status: 204 }))
      return jsonResponse({}, 404)
    })
    const browserUser = userEvent.setup()
    renderApp()

    const profileLink = await screen.findByRole('link', { name: /open profile for @sportsfan/i })
    expect(profileLink).toHaveAttribute('href', '/profile')
    await browserUser.click(profileLink)
    expect(await screen.findByRole('heading', { name: /your profile/i })).toBeInTheDocument()

    const email = screen.getByLabelText(/email address/i)
    const username = screen.getByLabelText(/^username$/i)
    await browserUser.clear(email)
    await browserUser.type(email, 'updated@example.com')
    await browserUser.clear(username)
    await browserUser.type(username, 'updated_fan')
    await browserUser.click(screen.getByRole('button', { name: /save profile/i }))
    expect(await screen.findByText(/verification email sent to updated@example.com/i)).toBeInTheDocument()
    expect(screen.getByText(/email change pending/i)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /open profile for @updated_fan/i })).toBeInTheDocument()

    await browserUser.type(screen.getByLabelText(/^current password$/i), 'SecurePass123!')
    await browserUser.type(screen.getByLabelText(/^new password$/i), 'NewSecurePass123!')
    await browserUser.type(screen.getByLabelText(/confirm new password/i), 'NewSecurePass123!')
    await browserUser.click(screen.getByRole('button', { name: /^change password$/i }))
    expect(await screen.findByText(/password has been changed/i)).toBeInTheDocument()

    await browserUser.click(screen.getByRole('button', { name: /delete user account/i }))
    await browserUser.type(screen.getByLabelText(/enter your current password/i), 'NewSecurePass123!')
    await browserUser.click(screen.getByRole('button', { name: /permanently delete account/i }))
    await waitFor(() => expect(localStorage.getItem('sportshub.access_token')).toBeNull())
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('/users/me'), expect.objectContaining({
      method: 'PATCH',
      headers: expect.objectContaining({ Authorization: 'Bearer token-1' }),
    }))
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('/users/me'), expect.objectContaining({
      method: 'DELETE',
      headers: expect.objectContaining({ Authorization: 'Bearer token-1' }),
    }))
  })

  it('verifies an email from the local mailbox link', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation((input, init) => {
      if (String(input).endsWith('/auth/verify-email') && init?.method === 'POST') return jsonResponse({
        id: 'user-1', email: 'fan@example.com', pending_email: null, email_verified: true, username: 'sportsfan', role: 'fan',
      })
      return jsonResponse({}, 404)
    })
    renderApp('/verify-email?token=signed-email-token')
    expect(await screen.findByRole('heading', { name: /email verified/i })).toBeInTheDocument()
    expect(screen.getByText(/verified for fan@example.com/i)).toBeInTheDocument()
    expect(screen.getAllByRole('link', { name: /sign in/i }).some((link) => link.getAttribute('href') === '/login')).toBe(true)
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('/auth/verify-email'), expect.objectContaining({ method: 'POST' }))
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

  it('removes a followed team only after inline confirmation', async () => {
    localStorage.setItem('sportshub.access_token', 'token-1')
    const arsenal = { id: 'team-1', api_team_id: 42, third_party_id: '42', name: 'Arsenal', country: 'England', logo_url: null }
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation((input, init) => {
      const url = String(input)
      if (url.endsWith('/auth/me')) return jsonResponse({ id: 'user-1', email: 'fan@example.com', username: 'sportsfan', role: 'fan' })
      if (url.endsWith('/notifications/inbox')) return jsonResponse({ unread_count: 0, total_items: 0, items: [] })
      if (url.endsWith('/users/me/team-preferences') && (!init || init.method !== 'PUT')) return jsonResponse([arsenal])
      if (url.endsWith('/users/me/team-preferences/team-1') && init?.method === 'DELETE') return jsonResponse(arsenal)
      return jsonResponse({}, 404)
    })
    const user = userEvent.setup()
    renderApp('/my/teams')
    const remove = await screen.findByRole('button', { name: /remove arsenal from your hub/i })
    await user.click(remove)
    expect(screen.getByText('Arsenal')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /confirm remove arsenal/i }))
    expect(await screen.findByText(/arsenal was removed from your hub/i)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /remove arsenal from your hub/i })).not.toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('/users/me/team-preferences/team-1'), expect.objectContaining({
      method: 'DELETE',
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
