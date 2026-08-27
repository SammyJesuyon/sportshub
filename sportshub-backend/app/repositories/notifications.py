from __future__ import annotations

from sqlalchemy import func, select, update

from app.db.models import UserAlert, UserNotificationPreference, UserPushDevice
from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository):
    """Persists notification preferences, devices, and inbox records."""

    def get_preferences(self, user_id: str) -> UserNotificationPreference | None:
        return self.session.get(UserNotificationPreference, user_id)

    def find_device(self, user_id: str, expo_push_token: str) -> UserPushDevice | None:
        return self.session.scalar(
            select(UserPushDevice).where(
                UserPushDevice.user_id == user_id,
                UserPushDevice.expo_push_token == expo_push_token,
            )
        )

    def inbox(self, user_id: str, limit: int) -> list[UserAlert]:
        return list(
            self.session.scalars(
                select(UserAlert)
                .where(UserAlert.user_id == user_id)
                .order_by(UserAlert.created_at.desc(), UserAlert.id.desc())
                .limit(limit)
            )
        )

    def unread_count(self, user_id: str) -> int:
        return int(
            self.session.scalar(
                select(func.count(UserAlert.id)).where(
                    UserAlert.user_id == user_id, UserAlert.is_read.is_(False)
                )
            )
            or 0
        )

    def total_count(self, user_id: str) -> int:
        return int(
            self.session.scalar(
                select(func.count(UserAlert.id)).where(UserAlert.user_id == user_id)
            )
            or 0
        )

    def find_alert(self, user_id: str, alert_id: str) -> UserAlert | None:
        return self.session.scalar(
            select(UserAlert).where(
                UserAlert.id == alert_id, UserAlert.user_id == user_id
            )
        )

    def mark_all_read(self, user_id: str) -> int:
        result = self.session.execute(
            update(UserAlert)
            .where(UserAlert.user_id == user_id, UserAlert.is_read.is_(False))
            .values(is_read=True)
        )
        return int(result.rowcount or 0)
