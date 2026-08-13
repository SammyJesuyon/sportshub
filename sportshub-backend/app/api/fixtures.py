from datetime import date
from math import ceil
from typing import Literal, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_sports_provider
from app.integrations.api_sports import (
    ProviderFixture,
    SportsProvider,
    fixture_bucket,
)
from app.schemas.fixture import (
    FixtureDetailResponse,
    FixtureResponse,
    MatchdayResponse,
)


router = APIRouter(prefix="/fixtures", tags=["fixtures"])
FixtureBucket = Literal["live", "half_time", "full_time", "scheduled"]


def fixture_response(fixture: ProviderFixture) -> FixtureResponse:
    return FixtureResponse(
        **{
            **fixture.__dict__,
            "home": fixture.home.__dict__,
            "away": fixture.away.__dict__,
        },
        bucket=fixture_bucket(fixture.status_short),
    )


@router.get("/matchday", response_model=MatchdayResponse)
def get_matchday(
    fixture_date: Optional[date] = Query(default=None, alias="date"),
    bucket: Optional[FixtureBucket] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=24),
    provider: SportsProvider = Depends(get_sports_provider),
):
    requested_date = fixture_date or date.today()
    try:
        snapshot = provider.matchday_snapshot(requested_date)
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Sports provider is temporarily unavailable",
        ) from exc

    fixtures = [fixture_response(fixture) for fixture in snapshot.fixtures]
    order = {"live": 0, "half_time": 1, "full_time": 2, "scheduled": 3}
    fixtures.sort(key=lambda fixture: (order[fixture.bucket], fixture.kickoff))
    counts = {
        item: sum(1 for fixture in fixtures if fixture.bucket == item)
        for item in order
    }
    filtered = [fixture for fixture in fixtures if bucket is None or fixture.bucket == bucket]
    total_items = len(filtered)
    total_pages = max(1, ceil(total_items / page_size))
    start = (page - 1) * page_size
    paginated = filtered[start : start + page_size]
    return MatchdayResponse(
        date=requested_date,
        timezone="UTC",
        bucket=bucket,
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
        counts=counts,
        fixtures=paginated,
    )


@router.get("/{fixture_id}", response_model=FixtureDetailResponse)
def get_fixture_detail(
    fixture_id: int,
    fixture_date: Optional[date] = Query(default=None, alias="date"),
    provider: SportsProvider = Depends(get_sports_provider),
):
    requested_date = fixture_date or date.today()
    try:
        matchday = provider.matchday_snapshot(requested_date)
        fixture = next(
            (item for item in matchday.fixtures if item.fixture_id == fixture_id), None
        )
        if fixture is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Fixture not found")
        snapshot = provider.fixture_detail(fixture)
    except HTTPException:
        raise
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Sports provider is temporarily unavailable",
        ) from exc

    detail = snapshot.detail
    return FixtureDetailResponse(
        fixture=fixture_response(detail.fixture),
        referee=detail.referee,
        venue_name=detail.venue_name,
        venue_city=detail.venue_city,
        halftime_home=detail.halftime_home,
        halftime_away=detail.halftime_away,
        fulltime_home=detail.fulltime_home,
        fulltime_away=detail.fulltime_away,
        extratime_home=detail.extratime_home,
        extratime_away=detail.extratime_away,
        penalty_home=detail.penalty_home,
        penalty_away=detail.penalty_away,
        events=[event.__dict__ for event in detail.events],
        statistics=[
            {
                **team.__dict__,
                "statistics": [statistic.__dict__ for statistic in team.statistics],
            }
            for team in detail.statistics
        ],
        lineups=[
            {
                **lineup.__dict__,
                "starting_xi": [player.__dict__ for player in lineup.starting_xi],
                "substitutes": [player.__dict__ for player in lineup.substitutes],
            }
            for lineup in detail.lineups
        ],
    )
