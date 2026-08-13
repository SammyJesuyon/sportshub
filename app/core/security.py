from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt


ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(user_id: str, secret_key: str, expires_minutes: int) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    return jwt.encode(
        {"sub": user_id, "type": "access", "exp": expires_at},
        secret_key,
        algorithm=ALGORITHM,
    )


def decode_access_token(token: str, secret_key: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
    except JWTError:
        return None
    if payload.get("type") != "access":
        return None
    subject = payload.get("sub")
    return subject if isinstance(subject, str) else None

