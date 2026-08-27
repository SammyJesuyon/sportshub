from fastapi import APIRouter, Depends, Request, status

from app.api.dependencies import get_current_user, get_user_repository
from app.db.models import User
from app.repositories.users import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services.auth import AuthService


router = APIRouter(prefix="/auth", tags=["authentication"])


def get_auth_service(
    request: Request,
    users: UserRepository = Depends(get_user_repository),
) -> AuthService:
    settings = request.app.state.settings
    return AuthService(users, settings.secret_key, settings.access_token_expire_minutes)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, service: AuthService = Depends(get_auth_service)):
    return service.register(body)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, service: AuthService = Depends(get_auth_service)):
    return service.login(body)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
