from fastapi import APIRouter, Depends, Request, status

from app.api.dependencies import get_current_user, get_user_repository
from app.db.models import User
from app.repositories.users import UserRepository
from app.schemas.auth import (
    EmailVerificationRequest,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth import AuthService


router = APIRouter(prefix="/auth", tags=["authentication"])


def get_auth_service(
    request: Request,
    users: UserRepository = Depends(get_user_repository),
) -> AuthService:
    settings = request.app.state.settings
    return AuthService(users, settings, request.app.state.email_sender)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, service: AuthService = Depends(get_auth_service)):
    return service.register(body)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, service: AuthService = Depends(get_auth_service)):
    return service.login(body)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/verify-email", response_model=UserResponse)
def verify_email(
    body: EmailVerificationRequest,
    service: AuthService = Depends(get_auth_service),
):
    return service.verify_email(body.token)
