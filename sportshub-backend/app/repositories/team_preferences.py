from __future__ import annotations

from collections.abc import Collection

from sqlalchemy import or_, select

from app.db.models import Team, UserTeamPreference
from app.repositories.base import BaseRepository
from app.repositories.teams import team_identity_filters


class TeamPreferenceRepository(BaseRepository):
    """Persists authenticated user-to-team associations."""

    def list_for_user(self, user_id: str) -> list[Team]:
        return list(
            self.session.scalars(
                select(Team)
                .join(UserTeamPreference, UserTeamPreference.team_id == Team.id)
                .where(UserTeamPreference.user_id == user_id)
                .order_by(Team.name)
            )
        )

    def resolve_team(self, supplied_id: str) -> Team | None:
        return self.session.scalar(
            select(Team).where(or_(*team_identity_filters(supplied_id)))
        )

    def existing_team_ids(
        self, user_id: str, team_ids: Collection[str]
    ) -> set[str]:
        if not team_ids:
            return set()
        return set(
            self.session.scalars(
                select(UserTeamPreference.team_id).where(
                    UserTeamPreference.user_id == user_id,
                    UserTeamPreference.team_id.in_(team_ids),
                )
            )
        )

    def find_followed_team(self, user_id: str, supplied_id: str) -> Team | None:
        return self.session.scalar(
            select(Team)
            .join(UserTeamPreference, UserTeamPreference.team_id == Team.id)
            .where(
                UserTeamPreference.user_id == user_id,
                or_(*team_identity_filters(supplied_id)),
            )
        )

    def find_association(
        self, user_id: str, team_id: str
    ) -> UserTeamPreference | None:
        return self.session.scalar(
            select(UserTeamPreference).where(
                UserTeamPreference.user_id == user_id,
                UserTeamPreference.team_id == team_id,
            )
        )
