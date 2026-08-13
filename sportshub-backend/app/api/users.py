from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.db.models import User
from app.schemas.team import TeamPreferenceResult, TeamPreferenceUpdate, TeamResponse
from app.services.teams import TeamPreferenceService


router = APIRouter(prefix="/users", tags=["user preferences"])


@router.get("/me/team-preferences", response_model=list[TeamResponse])
def list_team_preferences(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return TeamPreferenceService(db).list_for_user(current_user)


@router.put("/me/team-preferences", response_model=TeamPreferenceResult)
def update_team_preferences(
    body: TeamPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = TeamPreferenceService(db).append(current_user, body.team_ids)
    if not result.teams:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            {"message": "No supplied team could be resolved", "not_found_ids": result.not_found_ids},
        )
    return result

