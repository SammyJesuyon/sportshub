from datetime import date
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_sports_provider
from app.integrations.api_sports import SportsProvider, fixture_bucket
from app.schemas.fixture import FixtureResponse, MatchdayResponse


router = APIRouter(prefix="/fixtures", tags=["fixtures"])


@router.get("/matchday", response_model=MatchdayResponse)
def get_matchday(
    fixture_date: Optional[date] = Query(default=None, alias="date"),
    provider: SportsProvider = Depends(get_sports_provider),
):
    requested_date = fixture_date or date.today()
    try:
        fixtures = provider.fixtures_for_date(requested_date)
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Sports provider is temporarily unavailable",
        ) from exc

    normalized = []
    for fixture in fixtures:
        fixture_data = {
            **fixture.__dict__,
            "home": fixture.home.__dict__,
            "away": fixture.away.__dict__,
        }
        normalized.append(
            FixtureResponse(
                **fixture_data,
                bucket=fixture_bucket(fixture.status_short),
            )
        )
    order = {"live": 0, "half_time": 1, "full_time": 2, "scheduled": 3}
    normalized.sort(key=lambda fixture: (order[fixture.bucket], fixture.kickoff))
    return MatchdayResponse(date=requested_date, timezone="UTC", fixtures=normalized)
