from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import router as api_router
from app.core.config import Settings, get_settings
from app.db.base import Base
from app.db.session import create_session_factory
from app.integrations.api_sports import ApiSportsAdapter, SampleSportsAdapter, SportsProvider


def select_sports_provider(settings: Settings) -> SportsProvider:
    if settings.sports_provider == "api-sports":
        return ApiSportsAdapter(settings.api_sports_key, settings.api_sports_base_url)
    return SampleSportsAdapter()


def create_app(
    settings: Optional[Settings] = None,
    sports_provider: Optional[SportsProvider] = None,
) -> FastAPI:
    settings = settings or get_settings()
    settings.validate_runtime_safety()
    session_factory = create_session_factory(settings.database_url)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        Base.metadata.create_all(bind=session_factory.kw["bind"])
        yield

    app = FastAPI(
        title=settings.app_name,
        description="CS425-sized SportsHub fan engagement backend",
        version="0.1.0",
        lifespan=lifespan,
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

    return app


app = create_app()
