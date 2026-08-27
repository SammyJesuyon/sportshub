from typing import Generator, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.models import User
from app.integrations.api_sports import SportsProvider
from app.repositories.health import HealthRepository
from app.repositories.notifications import NotificationRepository
from app.repositories.team_preferences import TeamPreferenceRepository
from app.repositories.teams import TeamRepository
from app.repositories.users import UserRepository


bearer = HTTPBearer(auto_error=False)


def get_db(request: Request) -> Generator[Session, None, None]:
    db = request.app.state.session_factory()
    try:
        yield db
    finally:
        db.close()


def get_sports_provider(request: Request) -> SportsProvider:
    return request.app.state.sports_provider


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_team_repository(db: Session = Depends(get_db)) -> TeamRepository:
    return TeamRepository(db)


def get_team_preference_repository(
    db: Session = Depends(get_db),
) -> TeamPreferenceRepository:
    return TeamPreferenceRepository(db)


def get_notification_repository(
    db: Session = Depends(get_db),
) -> NotificationRepository:
    return NotificationRepository(db)


def get_health_repository(db: Session = Depends(get_db)) -> HealthRepository:
    return HealthRepository(db)


def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
    users: UserRepository = Depends(get_user_repository),
) -> User:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Bearer token required")
    user_id = decode_access_token(credentials.credentials, request.app.state.settings.secret_key)
    user = users.get(user_id) if user_id else None
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Administrator access required")
    return user
