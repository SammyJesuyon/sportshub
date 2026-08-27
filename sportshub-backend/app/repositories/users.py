from __future__ import annotations

from sqlalchemy import or_, select

from app.db.models import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    """Persists users and resolves authentication identities."""

    def get(self, user_id: str) -> User | None:
        return self.session.get(User, user_id)

    def find_duplicate(self, email: str, username: str) -> User | None:
        return self.session.scalar(
            select(User).where(or_(User.email == email, User.username == username))
        )

    def find_by_email(self, email: str) -> User | None:
        return self.session.scalar(select(User).where(User.email == email))
