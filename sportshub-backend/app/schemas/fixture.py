from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel


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
    fixtures: list[FixtureResponse]
