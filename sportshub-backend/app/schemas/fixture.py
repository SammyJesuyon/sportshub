from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field


class FixtureTeamResponse(BaseModel):
    provider_id: int
    name: str
    logo_url: Optional[str]
    goals: Optional[int]


class FixtureResponse(BaseModel):
    fixture_id: int
    kickoff: str
    timezone: str
    league_id: int
    league_name: str
    league_logo_url: Optional[str]
    status_short: str
    status_long: str
    elapsed: Optional[int]
    bucket: Literal["live", "half_time", "full_time", "scheduled"]
    home: FixtureTeamResponse
    away: FixtureTeamResponse


class MatchdayResponse(BaseModel):
    date: date
    timezone: str
    bucket: Optional[Literal["live", "half_time", "full_time", "scheduled"]]
    page: int
    page_size: int
    total_items: int
    total_pages: int
    counts: dict[str, int]
    fixtures: list[FixtureResponse]


class FixtureEventResponse(BaseModel):
    elapsed: Optional[int]
    extra: Optional[int]
    team_name: str
    player_name: Optional[str]
    assist_name: Optional[str]
    event_type: str
    detail: str


class FixtureStatisticResponse(BaseModel):
    name: str
    value: Optional[str]


class FixtureTeamStatisticsResponse(BaseModel):
    provider_id: Optional[int]
    team_name: str
    logo_url: Optional[str]
    statistics: list[FixtureStatisticResponse]


class FixtureLineupPlayerResponse(BaseModel):
    provider_id: Optional[int]
    name: str
    number: Optional[int]
    position: Optional[str]
    grid: Optional[str]


class FixtureTeamLineupResponse(BaseModel):
    provider_id: Optional[int]
    team_name: str
    logo_url: Optional[str]
    formation: Optional[str]
    coach_name: Optional[str]
    starting_xi: list[FixtureLineupPlayerResponse]
    substitutes: list[FixtureLineupPlayerResponse]


class FixtureDetailResponse(BaseModel):
    fixture: FixtureResponse
    referee: Optional[str]
    venue_name: Optional[str]
    venue_city: Optional[str]
    halftime_home: Optional[int]
    halftime_away: Optional[int]
    fulltime_home: Optional[int]
    fulltime_away: Optional[int]
    extratime_home: Optional[int]
    extratime_away: Optional[int]
    penalty_home: Optional[int]
    penalty_away: Optional[int]
    events: list[FixtureEventResponse]
    statistics: list[FixtureTeamStatisticsResponse]
    lineups: list[FixtureTeamLineupResponse]


class PaginationQuery(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=12, ge=1, le=24)
