from sqlalchemy import text

from app.repositories.base import BaseRepository


class HealthRepository(BaseRepository):
    """Runs the minimal persistence probe used by database readiness checks."""

    def ping(self) -> None:
        self.session.execute(text("SELECT 1"))
