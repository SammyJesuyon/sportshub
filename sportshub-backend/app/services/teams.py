from typing import List, Optional, Union

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.models import Team, User, UserAlert, UserTeamPreference
from app.integrations.api_sports import SportsProvider
from app.schemas.team import TeamPreferenceResult


class TeamService:
    """Searches stable local teams first and warms them through the provider adapter."""

    def __init__(self, db: Session, provider: SportsProvider):
        self.db = db
        self.provider = provider

    def search(self, query: str) -> list[Team]:
        pattern = f"%{query}%"
        cached = list(
            self.db.scalars(
                select(Team).where(Team.name.ilike(pattern)).order_by(Team.name).limit(25)
            )
        )
        if cached:
            return cached

        provider_teams = self.provider.search_teams(query)
        for item in provider_teams:
            team = self.db.scalar(select(Team).where(Team.api_team_id == item.provider_id))
            if team is None:
                team = Team(
                    api_team_id=item.provider_id,
                    third_party_id=str(item.provider_id),
                    name=item.name,
                    country=item.country,
                    logo_url=item.logo_url,
                )
                self.db.add(team)
            else:
                team.name = item.name
                team.country = item.country
                team.logo_url = item.logo_url
        self.db.commit()
        return list(
            self.db.scalars(
                select(Team).where(Team.name.ilike(pattern)).order_by(Team.name).limit(25)
            )
        )


class TeamPreferenceService:
    """Owns authenticated user-to-team association updates."""

    def __init__(self, db: Session):
        self.db = db

    def list_for_user(self, user: User) -> list[Team]:
        return list(
            self.db.scalars(
                select(Team)
                .join(UserTeamPreference, UserTeamPreference.team_id == Team.id)
                .where(UserTeamPreference.user_id == user.id)
                .order_by(Team.name)
            )
        )

    def append(self, user: User, team_ids: List[Union[str, int]]) -> TeamPreferenceResult:
        resolved: dict[str, Team] = {}
        not_found: list[str] = []

        for supplied_id in team_ids:
            raw_id = str(supplied_id)
            filters = [Team.id == raw_id, Team.third_party_id == raw_id]
            if raw_id.isdigit():
                filters.append(Team.api_team_id == int(raw_id))
            team = self.db.scalar(select(Team).where(or_(*filters)))
            if team is None:
                not_found.append(raw_id)
            else:
                resolved[team.id] = team

        if not resolved:
            return TeamPreferenceResult(
                teams=[], added_count=0, duplicate_count=0, not_found_ids=not_found
            )

        existing_ids = set(
            self.db.scalars(
                select(UserTeamPreference.team_id).where(
                    UserTeamPreference.user_id == user.id,
                    UserTeamPreference.team_id.in_(resolved),
                )
            )
        )
        added_ids = set(resolved) - existing_ids
        self.db.add_all(
            UserTeamPreference(user_id=user.id, team_id=team_id) for team_id in added_ids
        )
        self.db.add_all(
            UserAlert(
                user_id=user.id,
                kind="team_followed",
                title=f"{resolved[team_id].name} added to your hub",
                summary=f"You are now following {resolved[team_id].name}. Matchday updates will appear here as inbox coverage expands.",
                link_url="/my/teams",
            )
            for team_id in added_ids
        )
        self.db.commit()
        return TeamPreferenceResult(
            teams=[resolved[key] for key in sorted(resolved, key=lambda key: resolved[key].name)],
            added_count=len(added_ids),
            duplicate_count=len(existing_ids),
            not_found_ids=not_found,
        )

    def remove(self, user: User, supplied_team_id: str) -> Optional[Team]:
        filters = [Team.id == supplied_team_id, Team.third_party_id == supplied_team_id]
        if supplied_team_id.isdigit():
            filters.append(Team.api_team_id == int(supplied_team_id))

        team = self.db.scalar(
            select(Team)
            .join(UserTeamPreference, UserTeamPreference.team_id == Team.id)
            .where(
                UserTeamPreference.user_id == user.id,
                or_(*filters),
            )
        )
        if team is None:
            return None

        association = self.db.scalar(
            select(UserTeamPreference).where(
                UserTeamPreference.user_id == user.id,
                UserTeamPreference.team_id == team.id,
            )
        )
        self.db.delete(association)
        self.db.commit()
        return team
