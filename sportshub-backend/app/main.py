from typing import Optional

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.dependencies import get_health_repository
from app.api.router import router as api_router
from app.core.config import Settings, get_settings
from app.db.session import create_session_factory
from app.integrations.api_sports import ApiSportsAdapter, SampleSportsAdapter, SportsProvider
from app.integrations.isports import ISportsAdapter
from app.repositories.health import HealthRepository


def select_sports_provider(settings: Settings) -> SportsProvider:
    if settings.sports_provider == "isports":
        return ISportsAdapter(
            settings.isports_api_key,
            settings.isports_base_url,
            settings.isports_fallback_base_url,
            settings.isports_cache_path,
        )
    if settings.sports_provider == "api-sports":
        return ApiSportsAdapter(
            settings.api_sports_key,
            settings.api_sports_base_url,
            settings.api_sports_cache_path,
        )
    return SampleSportsAdapter()


def create_app(
    settings: Optional[Settings] = None,
    sports_provider: Optional[SportsProvider] = None,
) -> FastAPI:
    settings = settings or get_settings()
    settings.validate_runtime_safety()
    session_factory = create_session_factory(settings.database_url)

    app = FastAPI(
        title=settings.app_name,
        description="CS425-sized SportsHub fan engagement backend",
        version="0.1.0",
    )
    app.state.settings = settings
    app.state.session_factory = session_factory
    app.state.sports_provider = sports_provider or select_sports_provider(settings)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router, prefix="/api/v1")

    @app.get("/health", tags=["operations"])
    def health():
        return {"status": "ok", "service": "sportshub-api"}

    @app.get("/health/ready", tags=["operations"])
    def readiness(health_repository: HealthRepository = Depends(get_health_repository)):
        health_repository.ping()
        return {"status": "ready", "database": "connected"}

    return app


app = create_app()
