from typing import Optional, Union

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.fixture import FixtureResponse


class TeamResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    api_team_id: Optional[int]
    league_provider_id: Optional[int]
    third_party_id: Optional[str]
    name: str
    country: Optional[str]
    logo_url: Optional[str]
    code: Optional[str]
    founded: Optional[int]
    national: Optional[bool]
    venue_name: Optional[str]
    venue_address: Optional[str]
    venue_city: Optional[str]
    venue_capacity: Optional[int]
    venue_surface: Optional[str]
    venue_image_url: Optional[str]


class TeamScheduleResponse(BaseModel):
    current_fixture: Optional[FixtureResponse]
    next_fixture: Optional[FixtureResponse]
    recent_fixture: Optional[FixtureResponse]


class TeamPreferenceUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    team_ids: list[Union[str, int]] = Field(min_length=1, max_length=20)


class TeamPreferenceResult(BaseModel):
    teams: list[TeamResponse]
    added_count: int
    duplicate_count: int
    not_found_ids: list[str]
