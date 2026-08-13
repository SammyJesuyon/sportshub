from typing import Optional

from pydantic import BaseModel


class ProviderQuotaResponse(BaseModel):
    daily_limit: Optional[int]
    daily_remaining: Optional[int]
    minute_limit: Optional[int]
    minute_remaining: Optional[int]
    observed_at: Optional[str]


class ProviderCacheResponse(BaseModel):
    matchday_entries: int
    fixture_detail_entries: int
    persistent: bool


class ProviderStatusResponse(BaseModel):
    quota: ProviderQuotaResponse
    cache: ProviderCacheResponse
