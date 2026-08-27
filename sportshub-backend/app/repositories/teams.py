from __future__ import annotations

from sqlalchemy import or_, select

from app.db.models import Team
from app.repositories.base import BaseRepository


def team_identity_filters(supplied_id: str):
    filters = [Team.id == supplied_id, Team.third_party_id == supplied_id]
    if supplied_id.isdigit():
        filters.append(Team.api_team_id == int(supplied_id))
    return filters


class TeamRepository(BaseRepository):
    """Persists stable internal teams and provider-derived team details."""

    def search_by_name(self, query: str, limit: int = 25) -> list[Team]:
        return list(
            self.session.scalars(
                select(Team)
                .where(Team.name.ilike(f"%{query}%"))
                .order_by(Team.name)
                .limit(limit)
            )
        )

    def find_by_provider_id(self, provider_id: int) -> Team | None:
        return self.session.scalar(
            select(Team).where(Team.api_team_id == provider_id)
        )

    def find_by_supplied_id(self, supplied_id: str) -> Team | None:
        return self.session.scalar(
            select(Team).where(or_(*team_identity_filters(supplied_id)))
        )
