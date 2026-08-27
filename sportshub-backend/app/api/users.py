from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_user, get_team_preference_repository
from app.db.models import User
from app.repositories.team_preferences import TeamPreferenceRepository
from app.schemas.team import TeamPreferenceResult, TeamPreferenceUpdate, TeamResponse
from app.services.teams import TeamPreferenceService


router = APIRouter(prefix="/users", tags=["user preferences"])


@router.get("/me/team-preferences", response_model=list[TeamResponse])
def list_team_preferences(
    current_user: User = Depends(get_current_user),
    preferences: TeamPreferenceRepository = Depends(get_team_preference_repository),
):
    return TeamPreferenceService(preferences).list_for_user(current_user)


@router.put("/me/team-preferences", response_model=TeamPreferenceResult)
def update_team_preferences(
    body: TeamPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    preferences: TeamPreferenceRepository = Depends(get_team_preference_repository),
):
    result = TeamPreferenceService(preferences).append(current_user, body.team_ids)
    if not result.teams:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            {"message": "No supplied team could be resolved", "not_found_ids": result.not_found_ids},
        )
    return result


@router.delete("/me/team-preferences/{team_id}", response_model=TeamResponse)
def remove_team_preference(
    team_id: str,
    current_user: User = Depends(get_current_user),
    preferences: TeamPreferenceRepository = Depends(get_team_preference_repository),
):
    team = TeamPreferenceService(preferences).remove(current_user, team_id)
    if team is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Followed team not found")
    return team
