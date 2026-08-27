from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_current_user, get_notification_repository
from app.db.models import User
from app.repositories.notifications import NotificationRepository
from app.schemas.notification import (
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
    AlertInboxResponse,
    AlertReadAllResponse,
    AlertResponse,
    PushDeviceRequest,
    PushDeviceResponse,
)
from app.services.notifications import NotificationService


router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/inbox", response_model=AlertInboxResponse)
def get_inbox(
    limit: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    notifications: NotificationRepository = Depends(get_notification_repository),
):
    alerts, unread_count, total_items = NotificationService(notifications).inbox(
        current_user, limit
    )
    return AlertInboxResponse(
        unread_count=unread_count,
        total_items=total_items,
        items=[AlertResponse.model_validate(alert) for alert in alerts],
    )


@router.put("/inbox/{alert_id}/read", response_model=AlertResponse)
def mark_alert_read(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    notifications: NotificationRepository = Depends(get_notification_repository),
):
    alert = NotificationService(notifications).mark_read(current_user, alert_id)
    if alert is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Alert not found")
    return alert


@router.put("/inbox/read-all", response_model=AlertReadAllResponse)
def mark_all_alerts_read(
    current_user: User = Depends(get_current_user),
    notifications: NotificationRepository = Depends(get_notification_repository),
):
    return AlertReadAllResponse(
        updated_count=NotificationService(notifications).mark_all_read(current_user)
    )


@router.get("/preferences", response_model=NotificationPreferenceResponse)
def get_preferences(
    current_user: User = Depends(get_current_user),
    notifications: NotificationRepository = Depends(get_notification_repository),
):
    return NotificationService(notifications).get_or_create_preferences(current_user)


@router.put("/preferences", response_model=NotificationPreferenceResponse)
def update_preferences(
    body: NotificationPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    notifications: NotificationRepository = Depends(get_notification_repository),
):
    return NotificationService(notifications).update_preferences(current_user, body)


@router.post(
    "/devices", response_model=PushDeviceResponse, status_code=status.HTTP_201_CREATED
)
def register_device(
    body: PushDeviceRequest,
    current_user: User = Depends(get_current_user),
    notifications: NotificationRepository = Depends(get_notification_repository),
):
    device = NotificationService(notifications).upsert_device(
        current_user, body.expo_push_token
    )
    return PushDeviceResponse(
        id=device.id,
        expo_push_token=device.expo_push_token,
        is_active=device.is_active,
    )
