from typing import Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class TeamResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    api_team_id: Optional[int]
    third_party_id: Optional[str]
    name: str
    country: Optional[str]
    logo_url: Optional[str]


class TeamPreferenceUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    team_ids: list[Union[str, int]] = Field(min_length=1, max_length=20)


class TeamPreferenceResult(BaseModel):
    teams: list[TeamResponse]
    added_count: int
    duplicate_count: int
    not_found_ids: list[str]
