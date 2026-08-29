from fastapi import HTTPException, status

from app.core.config import Settings
from app.core.security import hash_password, verify_password
from app.db.models import User
from app.integrations.email import EmailSender
from app.repositories.users import UserRepository
from app.schemas.auth import UserResponse
from app.schemas.user import UserAccountDelete, UserPasswordChange, UserProfileUpdate
from app.services.account_email import (
    send_password_changed_email,
    send_verification_email,
)


class UserAccountService:
    def __init__(
        self, users: UserRepository, settings: Settings, email_sender: EmailSender
    ):
        self.users = users
        self.settings = settings
        self.email_sender = email_sender

    def update_profile(
        self, user: User, request: UserProfileUpdate
    ) -> UserResponse:
        email = str(request.email) if request.email is not None else None
        conflict = self.users.find_profile_conflict(user.id, email, request.username)
        if conflict is not None:
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Email or username already exists"
            )

        should_send_verification = email is not None and email != user.email
        if email is not None:
            user.pending_email = email if should_send_verification else None
        if request.username is not None:
            user.username = request.username
        self.users.commit()
        self.users.refresh(user)
        if should_send_verification and user.pending_email is not None:
            send_verification_email(
                self.email_sender,
                self.settings,
                user,
                user.pending_email,
                "change_email",
            )
        return UserResponse.model_validate(user)

    def resend_email_verification(self, user: User) -> None:
        if user.pending_email is not None:
            email = user.pending_email
            purpose = "change_email"
        elif not user.email_verified:
            email = user.email
            purpose = "verify_email"
        else:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "The current email address is already verified",
            )
        send_verification_email(
            self.email_sender, self.settings, user, email, purpose
        )

    def change_password(self, user: User, request: UserPasswordChange) -> None:
        if not verify_password(request.current_password, user.password_hash):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, "Current password is incorrect"
            )
        if verify_password(request.new_password, user.password_hash):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "New password must be different from the current password",
            )
        user.password_hash = hash_password(request.new_password)
        self.users.commit()
        send_password_changed_email(self.email_sender, user)

    def delete_account(self, user: User, request: UserAccountDelete) -> None:
        if not verify_password(request.password, user.password_hash):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, "Current password is incorrect"
            )
        self.users.delete(user)
        self.users.commit()
