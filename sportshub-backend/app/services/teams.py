from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Union

import httpx

from app.db.models import Team, User, UserAlert, UserTeamPreference, utc_now
from app.integrations.api_sports import (
    ProviderFixture,
    ProviderTeam,
    SportsProvider,
    fixture_bucket,
)
from app.repositories.team_preferences import TeamPreferenceRepository
from app.repositories.teams import TeamRepository
from app.schemas.team import TeamPreferenceResult


@dataclass(frozen=True)
class TeamSchedule:
    current_fixture: Optional[ProviderFixture]
    next_fixture: Optional[ProviderFixture]
    recent_fixture: Optional[ProviderFixture]


class TeamService:
    """Searches stable local teams first and warms them through the provider adapter."""

    def __init__(self, teams: TeamRepository, provider: SportsProvider):
        self.teams = teams
        self.provider = provider

    def search(self, query: str) -> list[Team]:
        cached = self.teams.search_by_name(query)
        try:
            provider_teams = self.provider.search_teams(query)
        except (httpx.HTTPError, ValueError):
            if cached:
                return cached
            raise
        resolved_teams: list[Team] = []
        for item in provider_teams:
            team = self.teams.find_by_provider_id(item.provider_id)
            if team is None:
                team = Team(
                    api_team_id=item.provider_id,
                    third_party_id=str(item.provider_id),
                )
                self.teams.add(team)
            self._apply_provider_details(team, item)
            resolved_teams.append(team)
        self.teams.commit()
        return resolved_teams[:25]

    def schedule(self, supplied_id: str) -> Optional[TeamSchedule]:
        team = self.teams.find_by_supplied_id(supplied_id)
        if team is None:
            return None
        if team.api_team_id is None:
            return TeamSchedule(None, None, None)
        if team.league_provider_id is None:
            provider_team = self.provider.get_team(team.api_team_id)
            if provider_team is not None:
                self._apply_provider_details(team, provider_team)
                self.teams.commit()
                self.teams.refresh(team)

        fixtures = self.provider.team_schedule(
            team.api_team_id, team.league_provider_id
        )
        now = datetime.now(timezone.utc)

        def kickoff(fixture: ProviderFixture) -> datetime:
            value = datetime.fromisoformat(fixture.kickoff.replace("Z", "+00:00"))
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)

        current = sorted(
            (
                fixture
                for fixture in fixtures
                if fixture_bucket(fixture.status_short) in {"live", "half_time"}
            ),
            key=kickoff,
        )
        upcoming = sorted(
            (
                fixture
                for fixture in fixtures
                if fixture_bucket(fixture.status_short) == "scheduled"
                and kickoff(fixture) >= now
            ),
            key=kickoff,
        )
        recent = sorted(
            (
                fixture
                for fixture in fixtures
                if fixture_bucket(fixture.status_short) == "full_time"
                or kickoff(fixture) < now
            ),
            key=kickoff,
            reverse=True,
        )
        return TeamSchedule(
            current_fixture=current[0] if current else None,
            next_fixture=upcoming[0] if upcoming else None,
            recent_fixture=recent[0] if recent else None,
        )

    def get(self, supplied_id: str) -> Optional[Team]:
        team = self.teams.find_by_supplied_id(supplied_id)
        if team is None:
            return None
        refresh_after = utc_now() - timedelta(days=1)
        should_refresh = (
            not team.details_loaded
            and team.api_team_id is not None
            and (
                team.details_checked_at is None
                or team.details_checked_at < refresh_after
            )
        )
        if should_refresh:
            team.details_checked_at = utc_now()
            try:
                provider_team = self.provider.get_team(team.api_team_id)
            except (httpx.HTTPError, ValueError):
                self.teams.commit()
                self.teams.refresh(team)
                return team
            if provider_team is not None:
                self._apply_provider_details(team, provider_team)
            self.teams.commit()
            self.teams.refresh(team)
        return team

    @staticmethod
    def _apply_provider_details(team: Team, item: ProviderTeam) -> None:
        team.name = item.name
        team.country = item.country
        team.logo_url = item.logo_url
        team.code = item.code
        team.founded = item.founded
        team.national = item.national
        team.venue_name = item.venue_name
        team.venue_address = item.venue_address
        team.venue_city = item.venue_city
        team.venue_capacity = item.venue_capacity
        team.venue_surface = item.venue_surface
        team.venue_image_url = item.venue_image_url
        if item.league_provider_id is not None:
            team.league_provider_id = item.league_provider_id
        team.details_loaded = True
        team.details_checked_at = utc_now()


class TeamPreferenceService:
    """Owns authenticated user-to-team association updates."""

    def __init__(self, preferences: TeamPreferenceRepository):
        self.preferences = preferences

    def list_for_user(self, user: User) -> list[Team]:
        return self.preferences.list_for_user(user.id)

    def append(self, user: User, team_ids: List[Union[str, int]]) -> TeamPreferenceResult:
        resolved: dict[str, Team] = {}
        not_found: list[str] = []

        for supplied_id in team_ids:
            raw_id = str(supplied_id)
            team = self.preferences.resolve_team(raw_id)
            if team is None:
                not_found.append(raw_id)
            else:
                resolved[team.id] = team

        if not resolved:
            return TeamPreferenceResult(
                teams=[], added_count=0, duplicate_count=0, not_found_ids=not_found
            )

        existing_ids = self.preferences.existing_team_ids(user.id, resolved.keys())
        added_ids = set(resolved) - existing_ids
        self.preferences.add_all(
            UserTeamPreference(user_id=user.id, team_id=team_id) for team_id in added_ids
        )
        self.preferences.add_all(
            UserAlert(
                user_id=user.id,
                kind="team_followed",
                title=f"{resolved[team_id].name} added to your hub",
                summary=f"You are now following {resolved[team_id].name}. Matchday updates will appear here as inbox coverage expands.",
                link_url="/my/teams",
            )
            for team_id in added_ids
        )
        self.preferences.commit()
        return TeamPreferenceResult(
            teams=[resolved[key] for key in sorted(resolved, key=lambda key: resolved[key].name)],
            added_count=len(added_ids),
            duplicate_count=len(existing_ids),
            not_found_ids=not_found,
        )

    def remove(self, user: User, supplied_team_id: str) -> Optional[Team]:
        team = self.preferences.find_followed_team(user.id, supplied_team_id)
        if team is None:
            return None

        association = self.preferences.find_association(user.id, team.id)
        if association is None:
            return None
        self.preferences.delete(association)
        self.preferences.commit()
        return team
