import type { AlertInbox, AlertItem, FixtureBucket, FixtureDetail, Matchday, NotificationPreferences, Team, TeamPreferenceResult, TokenResponse } from './types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8010/api/v1'

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

function errorMessage(payload: unknown): string {
  if (payload && typeof payload === 'object' && 'detail' in payload) {
    const detail = payload.detail
    if (typeof detail === 'string') return detail
  }
  return 'SportsHub could not complete that request.'
}

async function request<T>(path: string, options: RequestInit = {}, token?: string): Promise<T> {
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> | undefined),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }
  if (options.body !== undefined) headers['Content-Type'] = 'application/json'
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  })
  const payload = await response.json().catch(() => null)
  if (!response.ok) throw new ApiError(response.status, errorMessage(payload))
  return payload as T
}

export const api = {
  register: (body: { email: string; username: string; password: string }) =>
    request<TokenResponse>('/auth/register', { method: 'POST', body: JSON.stringify(body) }),
  login: (body: { email: string; password: string }) =>
    request<TokenResponse>('/auth/login', { method: 'POST', body: JSON.stringify(body) }),
  me: (token: string) => request<TokenResponse['user']>('/auth/me', {}, token),
  matchday: (bucket: FixtureBucket, page = 1, pageSize = 12, date?: string, timezone?: string) => request<Matchday>(
    `/fixtures/matchday?bucket=${bucket}&page=${page}&page_size=${pageSize}${date ? `&date=${encodeURIComponent(date)}` : ''}${timezone ? `&timezone=${encodeURIComponent(timezone)}` : ''}`,
  ),
  fixtureDetail: (fixtureId: number, fixtureDate: string, timezone?: string) => request<FixtureDetail>(
    `/fixtures/${fixtureId}?date=${encodeURIComponent(fixtureDate)}${timezone ? `&timezone=${encodeURIComponent(timezone)}` : ''}`,
  ),
  searchTeams: (query: string) => request<Team[]>(`/teams/?search=${encodeURIComponent(query)}`),
  followedTeams: (token: string) => request<Team[]>('/users/me/team-preferences', {}, token),
  followTeam: (token: string, teamId: string) => request<TeamPreferenceResult>(
    '/users/me/team-preferences',
    { method: 'PUT', body: JSON.stringify({ team_ids: [teamId] }) },
    token,
  ),
  notificationPreferences: (token: string) => request<NotificationPreferences>('/notifications/preferences', {}, token),
  updateNotificationPreferences: (token: string, preferences: Partial<NotificationPreferences>) => request<NotificationPreferences>(
    '/notifications/preferences',
    { method: 'PUT', body: JSON.stringify(preferences) },
    token,
  ),
  alertInbox: (token: string) => request<AlertInbox>('/notifications/inbox', {}, token),
  markAlertRead: (token: string, alertId: string) => request<AlertItem>(
    `/notifications/inbox/${encodeURIComponent(alertId)}/read`,
    { method: 'PUT' },
    token,
  ),
  markAllAlertsRead: (token: string) => request<{ updated_count: number }>(
    '/notifications/inbox/read-all',
    { method: 'PUT' },
    token,
  ),
}
