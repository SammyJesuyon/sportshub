from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import User, UserNotificationPreference, UserPushDevice
from app.schemas.notification import NotificationPreferenceUpdate


class NotificationService:
    """Stores global-per-user toggles and push device registrations."""

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

