from fastapi import APIRouter, Depends

from app.api.dependencies import get_sports_provider, require_admin
from app.db.models import User
from app.integrations.api_sports import SportsProvider
from app.schemas.admin import (
    ProviderCacheResponse,
    ProviderQuotaResponse,
    ProviderStatusResponse,
)


router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/provider-status", response_model=ProviderStatusResponse)
def get_provider_status(
    _: User = Depends(require_admin),
    provider: SportsProvider = Depends(get_sports_provider),
):
    status = provider.operational_status()
    return ProviderStatusResponse(
        quota=ProviderQuotaResponse(**status.quota.__dict__),
        cache=ProviderCacheResponse(
            matchday_entries=status.matchday_cache_entries,
            fixture_detail_entries=status.fixture_detail_cache_entries,
            persistent=status.persistent_cache_enabled,
        ),
    )
