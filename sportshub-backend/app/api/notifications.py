from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.db.models import User
from app.schemas.notification import (
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
    PushDeviceRequest,
    PushDeviceResponse,
)
from app.services.notifications import NotificationService


router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/preferences", response_model=NotificationPreferenceResponse)
def get_preferences(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return NotificationService(db).get_or_create_preferences(current_user)


@router.put("/preferences", response_model=NotificationPreferenceResponse)
def update_preferences(
    body: NotificationPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return NotificationService(db).update_preferences(current_user, body)


@router.post(
    "/devices", response_model=PushDeviceResponse, status_code=status.HTTP_201_CREATED
)
def register_device(
    body: PushDeviceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    device = NotificationService(db).upsert_device(current_user, body.expo_push_token)
    return PushDeviceResponse(
        id=device.id,
        expo_push_token=device.expo_push_token,
        is_active=device.is_active,
    )

