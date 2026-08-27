from typing import Optional

from app.db.models import User, UserAlert, UserNotificationPreference, UserPushDevice
from app.repositories.notifications import NotificationRepository
from app.schemas.notification import NotificationPreferenceUpdate


class NotificationService:
    """Owns each user's persisted inbox, preferences, and device records."""

    def __init__(self, notifications: NotificationRepository):
        self.notifications = notifications

    def get_or_create_preferences(self, user: User) -> UserNotificationPreference:
        preferences = self.notifications.get_preferences(user.id)
        if preferences is None:
            preferences = UserNotificationPreference(user_id=user.id)
            self.notifications.add(preferences)
            self.notifications.commit()
            self.notifications.refresh(preferences)
        return preferences

    def update_preferences(
        self, user: User, update: NotificationPreferenceUpdate
    ) -> UserNotificationPreference:
        preferences = self.notifications.get_preferences(user.id)
        if preferences is None:
            preferences = UserNotificationPreference(user_id=user.id)
            self.notifications.add(preferences)
        for name, value in update.model_dump(exclude_unset=True).items():
            setattr(preferences, name, value)
        self.notifications.commit()
        self.notifications.refresh(preferences)
        return preferences

    def upsert_device(self, user: User, expo_push_token: str) -> UserPushDevice:
        device = self.notifications.find_device(user.id, expo_push_token)
        if device is None:
            device = UserPushDevice(user_id=user.id, expo_push_token=expo_push_token)
            self.notifications.add(device)
        else:
            device.is_active = True
        self.notifications.commit()
        self.notifications.refresh(device)
        return device

    def inbox(self, user: User, limit: int = 50) -> tuple[list[UserAlert], int, int]:
        alerts = self.notifications.inbox(user.id, limit)
        return (
            alerts,
            self.notifications.unread_count(user.id),
            self.notifications.total_count(user.id),
        )

    def mark_read(self, user: User, alert_id: str) -> Optional[UserAlert]:
        alert = self.notifications.find_alert(user.id, alert_id)
        if alert is None:
            return None
        if not alert.is_read:
            alert.is_read = True
            self.notifications.commit()
            self.notifications.refresh(alert)
        return alert

    def mark_all_read(self, user: User) -> int:
        updated_count = self.notifications.mark_all_read(user.id)
        self.notifications.commit()
        return updated_count
