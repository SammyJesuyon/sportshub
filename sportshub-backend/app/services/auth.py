from fastapi import HTTPException, status

from app.core.config import Settings
from app.core.security import (
    create_access_token,
    decode_email_action_token,
    hash_password,
    verify_password,
)
from app.db.models import User, UserAlert, utc_now
from app.integrations.email import EmailSender
from app.repositories.users import UserRepository
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.account_email import (
    send_email_changed_notice,
    send_verification_email,
)


class AuthService:
    def __init__(
        self, users: UserRepository, settings: Settings, email_sender: EmailSender
    ):
        self.users = users
        self.settings = settings
        self.email_sender = email_sender

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
        send_verification_email(
            self.email_sender, self.settings, user, user.email, "verify_email"
        )
        return self._token_response(user)

    def login(self, request: LoginRequest) -> TokenResponse:
        user = self.users.find_by_email(str(request.email).lower())
        if not user or not user.is_active or not verify_password(request.password, user.password_hash):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
        return self._token_response(user)

    def _token_response(self, user: User) -> TokenResponse:
        token = create_access_token(
            user.id,
            self.settings.secret_key,
            self.settings.access_token_expire_minutes,
        )
        return TokenResponse(access_token=token, user=UserResponse.model_validate(user))

    def verify_email(self, token: str) -> UserResponse:
        decoded = decode_email_action_token(
            token, self.settings.secret_key, "verify_email"
        )
        purpose = "verify_email"
        if decoded is None:
            decoded = decode_email_action_token(
                token, self.settings.secret_key, "change_email"
            )
            purpose = "change_email"
        if decoded is None:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "Verification link is invalid or has expired",
            )

        user_id, email = decoded
        user = self.users.get(user_id)
        if user is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User account not found")

        if purpose == "verify_email":
            if user.email != email:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST, "Verification link is no longer valid"
                )
            user.email_verified_at = utc_now()
        else:
            if user.pending_email != email:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST, "Verification link is no longer valid"
                )
            if self.users.find_profile_conflict(user.id, email, None) is not None:
                raise HTTPException(
                    status.HTTP_409_CONFLICT, "Email address is no longer available"
                )
            old_email = user.email
            user.email = email
            user.pending_email = None
            user.email_verified_at = utc_now()
            self.users.commit()
            self.users.refresh(user)
            send_email_changed_notice(self.email_sender, user, old_email)
            return UserResponse.model_validate(user)

        self.users.commit()
        self.users.refresh(user)
        return UserResponse.model_validate(user)
