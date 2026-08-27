import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.api.dependencies import get_sports_provider, get_team_repository
from app.integrations.api_sports import SportsProvider
from app.repositories.teams import TeamRepository
from app.schemas.team import TeamResponse, TeamScheduleResponse
from app.api.fixtures import fixture_response
from app.services.teams import TeamService


router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("/", response_model=list[TeamResponse])
def search_teams(
    search: str = Query(min_length=2, max_length=80),
    teams: TeamRepository = Depends(get_team_repository),
    provider: SportsProvider = Depends(get_sports_provider),
):
    try:
        return TeamService(teams, provider).search(search)
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Sports provider is temporarily unavailable",
        ) from exc


@router.get("/{team_id}", response_model=TeamResponse)
def get_team(
    team_id: str,
    teams: TeamRepository = Depends(get_team_repository),
    provider: SportsProvider = Depends(get_sports_provider),
):
    try:
        team = TeamService(teams, provider).get(team_id)
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Team details are temporarily unavailable",
        ) from exc
    if team is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Team not found")
    return team


@router.get("/{team_id}/schedule", response_model=TeamScheduleResponse)
def get_team_schedule(
    team_id: str,
    timezone_name: str = Query(default="UTC", alias="timezone", max_length=64),
    teams: TeamRepository = Depends(get_team_repository),
    provider: SportsProvider = Depends(get_sports_provider),
):
    try:
        requested_zone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid timezone") from exc
    try:
        schedule = TeamService(teams, provider).schedule(team_id)
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Team schedule is temporarily unavailable",
        ) from exc
    if schedule is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Team not found")
    return TeamScheduleResponse(
        current_fixture=(
            fixture_response(schedule.current_fixture, requested_zone)
            if schedule.current_fixture
            else None
        ),
        next_fixture=(
            fixture_response(schedule.next_fixture, requested_zone)
            if schedule.next_fixture
            else None
        ),
        recent_fixture=(
            fixture_response(schedule.recent_fixture, requested_zone)
            if schedule.recent_fixture
            else None
        ),
    )
