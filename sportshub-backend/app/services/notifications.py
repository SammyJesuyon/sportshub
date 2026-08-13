from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.db.models import User, UserAlert, UserNotificationPreference, UserPushDevice
from app.schemas.notification import NotificationPreferenceUpdate


class NotificationService:
    """Owns each user's persisted inbox, preferences, and device records."""

    def __init__(self, db: Session):
        self.db = db

    def get_or_create_preferences(self, user: User) -> UserNotificationPreference:
        preferences = self.db.get(UserNotificationPreference, user.id)
        if preferences is None:
            preferences = UserNotificationPreference(user_id=user.id)
            self.db.add(preferences)
            self.db.commit()
            self.db.refresh(preferences)
        return preferences

    def update_preferences(
        self, user: User, update: NotificationPreferenceUpdate
    ) -> UserNotificationPreference:
        preferences = self.db.get(UserNotificationPreference, user.id)
        if preferences is None:
            preferences = UserNotificationPreference(user_id=user.id)
            self.db.add(preferences)
        for name, value in update.model_dump(exclude_unset=True).items():
            setattr(preferences, name, value)
        self.db.commit()
        self.db.refresh(preferences)
        return preferences

    def upsert_device(self, user: User, expo_push_token: str) -> UserPushDevice:
        device = self.db.scalar(
            select(UserPushDevice).where(
                UserPushDevice.user_id == user.id,
                UserPushDevice.expo_push_token == expo_push_token,
            )
        )
        if device is None:
            device = UserPushDevice(user_id=user.id, expo_push_token=expo_push_token)
            self.db.add(device)
        else:
            device.is_active = True
        self.db.commit()
        self.db.refresh(device)
        return device

    def inbox(self, user: User, limit: int = 50) -> tuple[list[UserAlert], int, int]:
        alerts = list(
            self.db.scalars(
                select(UserAlert)
                .where(UserAlert.user_id == user.id)
                .order_by(UserAlert.created_at.desc(), UserAlert.id.desc())
                .limit(limit)
            )
        )
        unread_count = self.db.scalar(
            select(func.count(UserAlert.id)).where(
                UserAlert.user_id == user.id, UserAlert.is_read.is_(False)
            )
        ) or 0
        total_items = self.db.scalar(
            select(func.count(UserAlert.id)).where(UserAlert.user_id == user.id)
        ) or 0
        return alerts, int(unread_count), int(total_items)

    def mark_read(self, user: User, alert_id: str) -> Optional[UserAlert]:
        alert = self.db.scalar(
            select(UserAlert).where(
                UserAlert.id == alert_id, UserAlert.user_id == user.id
            )
        )
        if alert is None:
            return None
        if not alert.is_read:
            alert.is_read = True
            self.db.commit()
            self.db.refresh(alert)
        return alert

    def mark_all_read(self, user: User) -> int:
        result = self.db.execute(
            update(UserAlert)
            .where(UserAlert.user_id == user.id, UserAlert.is_read.is_(False))
            .values(is_read=True)
        )
        self.db.commit()
        return int(result.rowcount or 0)
