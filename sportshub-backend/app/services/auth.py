from fastapi import HTTPException, status

from app.core.security import create_access_token, hash_password, verify_password
from app.db.models import User, UserAlert
from app.repositories.users import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse


class AuthService:
    def __init__(
        self, users: UserRepository, secret_key: str, expires_minutes: int
    ):
        self.users = users
        self.secret_key = secret_key
        self.expires_minutes = expires_minutes

    def register(self, request: RegisterRequest) -> TokenResponse:
        duplicate = self.users.find_duplicate(str(request.email), request.username)
        if duplicate:
            raise HTTPException(status.HTTP_409_CONFLICT, "Email or username already exists")

        user = User(
            email=request.email,
            username=request.username,
            password_hash=hash_password(request.password),
        )
        self.users.add(user)
        self.users.flush()
        self.users.add(
            UserAlert(
                user_id=user.id,
                kind="welcome",
                title="Welcome to SportsHub",
                summary="Your fan profile is ready. Follow a team to personalize your matchday experience.",
                link_url="/my/teams",
            )
        )
        self.users.commit()
        self.users.refresh(user)
        return self._token_response(user)

    def login(self, request: LoginRequest) -> TokenResponse:
        user = self.users.find_by_email(str(request.email).lower())
        if not user or not user.is_active or not verify_password(request.password, user.password_hash):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
        return self._token_response(user)

    def _token_response(self, user: User) -> TokenResponse:
        token = create_access_token(user.id, self.secret_key, self.expires_minutes)
        return TokenResponse(access_token=token, user=UserResponse.model_validate(user))
