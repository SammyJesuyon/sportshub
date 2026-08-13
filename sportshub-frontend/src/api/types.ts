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
  bucket: FixtureBucket | null
  page: number
  page_size: number
  total_items: number
  total_pages: number
  counts: Record<FixtureBucket, number>
  cache: CacheStatus
  quota: ProviderQuota
  fixtures: Fixture[]
}

export interface ProviderQuota {
  daily_limit: number | null
  daily_remaining: number | null
  minute_limit: number | null
  minute_remaining: number | null
  observed_at: string | null
}

export interface CacheStatus {
  hit: boolean
  age_seconds: number
  ttl_seconds: number
}

export interface FixtureEvent {
  elapsed: number | null
  extra: number | null
  team_name: string
  player_name: string | null
  assist_name: string | null
  event_type: string
  detail: string
}

export interface FixtureDetail {
  fixture: Fixture
  referee: string | null
  venue_name: string | null
  venue_city: string | null
  halftime_home: number | null
  halftime_away: number | null
  fulltime_home: number | null
  fulltime_away: number | null
  extratime_home: number | null
  extratime_away: number | null
  penalty_home: number | null
  penalty_away: number | null
  events: FixtureEvent[]
  cache: CacheStatus
  quota: ProviderQuota
}
