from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.api.dependencies import (
    get_current_user,
    get_team_preference_repository,
    get_user_repository,
)
from app.db.models import User
from app.repositories.team_preferences import TeamPreferenceRepository
from app.repositories.users import UserRepository
from app.schemas.auth import UserResponse
from app.schemas.team import TeamPreferenceResult, TeamPreferenceUpdate, TeamResponse
from app.schemas.user import UserAccountDelete, UserPasswordChange, UserProfileUpdate
from app.services.teams import TeamPreferenceService
from app.services.users import UserAccountService


router = APIRouter(prefix="/users", tags=["users"])


def get_user_account_service(
    request: Request,
    users: UserRepository = Depends(get_user_repository),
) -> UserAccountService:
    return UserAccountService(
        users, request.app.state.settings, request.app.state.email_sender
    )


@router.patch("/me", response_model=UserResponse)
def update_profile(
    body: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    service: UserAccountService = Depends(get_user_account_service),
):
    return service.update_profile(current_user, body)


@router.post("/me/email-verification", status_code=status.HTTP_202_ACCEPTED)
def resend_email_verification(
    current_user: User = Depends(get_current_user),
    service: UserAccountService = Depends(get_user_account_service),
):
    service.resend_email_verification(current_user)
    return {"message": "Verification email sent"}


@router.put("/me/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    body: UserPasswordChange,
    current_user: User = Depends(get_current_user),
    service: UserAccountService = Depends(get_user_account_service),
):
    service.change_password(current_user, body)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    body: UserAccountDelete,
    current_user: User = Depends(get_current_user),
    service: UserAccountService = Depends(get_user_account_service),
):
    service.delete_account(current_user, body)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


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
