from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class NotificationPreferenceUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: Optional[bool] = None
    pre_match_reminder: Optional[bool] = None
    match_start: Optional[bool] = None
    match_end: Optional[bool] = None


class NotificationPreferenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    enabled: bool
    pre_match_reminder: bool
    match_start: bool
    match_end: bool


class PushDeviceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expo_push_token: str = Field(min_length=10, max_length=255, pattern=r"^ExponentPushToken\[.+\]$")


class PushDeviceResponse(BaseModel):
    id: str
    expo_push_token: str
    is_active: bool
