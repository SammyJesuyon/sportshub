from __future__ import annotations

from sqlalchemy import and_, or_, select

from app.db.models import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    """Persists users and resolves authentication identities."""

    def get(self, user_id: str) -> User | None:
        return self.session.get(User, user_id)

    def find_duplicate(self, email: str, username: str) -> User | None:
        return self.session.scalar(
            select(User).where(
                or_(
                    User.email == email,
                    User.pending_email == email,
                    User.username == username,
                )
            )
        )

    def find_profile_conflict(
        self, user_id: str, email: str | None, username: str | None
    ) -> User | None:
        candidates = []
        if email is not None:
            candidates.extend((User.email == email, User.pending_email == email))
        if username is not None:
            candidates.append(User.username == username)
        if not candidates:
            return None
        return self.session.scalar(
            select(User).where(and_(User.id != user_id, or_(*candidates)))
        )

    def find_by_email(self, email: str) -> User | None:
        return self.session.scalar(select(User).where(User.email == email))
