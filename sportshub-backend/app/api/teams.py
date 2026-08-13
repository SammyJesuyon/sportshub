import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_sports_provider
from app.integrations.api_sports import SportsProvider
from app.schemas.team import TeamResponse
from app.services.teams import TeamService


router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("/", response_model=list[TeamResponse])
def search_teams(
    search: str = Query(min_length=2, max_length=80),
    db: Session = Depends(get_db),
    provider: SportsProvider = Depends(get_sports_provider),
):
    try:
        return TeamService(db, provider).search(search)
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Sports provider is temporarily unavailable",
        ) from exc
