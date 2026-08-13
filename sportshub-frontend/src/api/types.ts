export interface User {
  id: string
  email: string
  username: string
  role: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: User
}

export interface Team {
  id: string
  api_team_id: number | null
  third_party_id: string | null
  name: string
  country: string | null
  logo_url: string | null
}

export interface TeamPreferenceResult {
  teams: Team[]
  added_count: number
  duplicate_count: number
  not_found_ids: string[]
}

export interface NotificationPreferences {
  enabled: boolean
  pre_match_reminder: boolean
  match_start: boolean
  match_end: boolean
}

export type FixtureBucket = 'live' | 'half_time' | 'full_time' | 'scheduled'

export interface FixtureTeam {
  provider_id: number
  name: string
  logo_url: string | null
  goals: number | null
}

export interface Fixture {
  fixture_id: number
  kickoff: string
  timezone: string
  league_id: number
  league_name: string
  league_logo_url: string | null
  status_short: string
  status_long: string
  elapsed: number | null
  bucket: FixtureBucket
  home: FixtureTeam
  away: FixtureTeam
}

export interface Matchday {
  date: string
  timezone: string
  fixtures: Fixture[]
}
