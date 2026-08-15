from dataclasses import replace
from datetime import date, datetime, time, timezone
from math import ceil
from typing import Literal, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

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


def local_matchday_utc_dates(requested_date: date, requested_zone: ZoneInfo) -> list[date]:
    local_start = datetime.combine(requested_date, time.min, requested_zone)
    local_end = datetime.combine(requested_date, time.max, requested_zone)
    start_date = local_start.astimezone(timezone.utc).date()
    end_date = local_end.astimezone(timezone.utc).date()
    return [start_date] if start_date == end_date else [start_date, end_date]


def fixture_is_on_local_date(
    fixture: ProviderFixture, requested_date: date, requested_zone: ZoneInfo
) -> bool:
    return fixture_kickoff(fixture).astimezone(requested_zone).date() == requested_date


def fixture_kickoff(fixture: ProviderFixture) -> datetime:
    """Return an aware kickoff instant, including for provider timestamps without an offset."""
    kickoff = datetime.fromisoformat(fixture.kickoff.replace("Z", "+00:00"))
    if kickoff.tzinfo is not None:
        return kickoff
    try:
        provider_zone = ZoneInfo(fixture.timezone)
    except ZoneInfoNotFoundError:
        provider_zone = timezone.utc
    return kickoff.replace(tzinfo=provider_zone)


def fixture_response(
    fixture: ProviderFixture, requested_zone: ZoneInfo = ZoneInfo("UTC")
) -> FixtureResponse:
    local_fixture = replace(
        fixture,
        kickoff=fixture_kickoff(fixture).astimezone(requested_zone).isoformat(),
        timezone=requested_zone.key,
    )
    return FixtureResponse(
        **{
            **local_fixture.__dict__,
            "home": local_fixture.home.__dict__,
            "away": local_fixture.away.__dict__,
        },
        bucket=fixture_bucket(local_fixture.status_short),
    )


@router.get("/matchday", response_model=MatchdayResponse)
def get_matchday(
    fixture_date: Optional[date] = Query(default=None, alias="date"),
    timezone_name: str = Query(default="UTC", alias="timezone", max_length=64),
    bucket: Optional[FixtureBucket] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=24),
    provider: SportsProvider = Depends(get_sports_provider),
):
    try:
        requested_zone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid timezone") from exc
    requested_date = fixture_date or datetime.now(requested_zone).date()
    try:
        snapshots = [
            provider.matchday_snapshot(utc_date)
            for utc_date in local_matchday_utc_dates(requested_date, requested_zone)
        ]
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Sports provider is temporarily unavailable",
        ) from exc

    unique_fixtures = {
        fixture.fixture_id: fixture
        for snapshot in snapshots
        for fixture in snapshot.fixtures
        if fixture_is_on_local_date(fixture, requested_date, requested_zone)
    }
    fixtures = [
        fixture_response(fixture, requested_zone)
        for fixture in unique_fixtures.values()
    ]
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
        timezone=requested_zone.key,
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
    timezone_name: str = Query(default="UTC", alias="timezone", max_length=64),
    provider: SportsProvider = Depends(get_sports_provider),
):
    try:
        requested_zone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid timezone") from exc
    requested_date = fixture_date or datetime.now(requested_zone).date()
    try:
        matchdays = [
            provider.matchday_snapshot(utc_date)
            for utc_date in local_matchday_utc_dates(requested_date, requested_zone)
        ]
        fixture = next(
            (
                item
                for matchday in matchdays
                for item in matchday.fixtures
                if item.fixture_id == fixture_id
            ),
            None,
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
        fixture=fixture_response(detail.fixture, requested_zone),
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
