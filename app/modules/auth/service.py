from datetime import datetime, timedelta, timezone
from app.core.security import hash_password
from app.modules.auth.models import Role
from app.modules.auth.schemas import RegisterRequest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_token,
    verify_password,
)
from app.modules.auth.models import RefreshToken, User
from app.modules.auth.schemas import TokenResponse


def authenticate(db: Session, login: str, password: str) -> User | None:
    user = db.scalar(select(User).where(User.login == login, User.is_deleted.is_(False)))
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


def issue_tokens(
    db: Session, user: User, user_agent: str | None, ip: str | None
) -> TokenResponse:
    raw_refresh = generate_refresh_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_token(raw_refresh),
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            user_agent=(user_agent or "")[:255] or None,
            ip=ip,
        )
    )
    db.commit()
    return TokenResponse(
        access_token=create_access_token(user.id, user.role.name),
        refresh_token=raw_refresh,
    )


def refresh_tokens(
    db: Session, raw_refresh: str, user_agent: str | None, ip: str | None
) -> TokenResponse | None:
    token = db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw_refresh))
    )
    now = datetime.now(timezone.utc)
    if not token or token.revoked_at or token.expires_at <= now:
        return None
    user = db.get(User, token.user_id)
    if not user or user.is_deleted:
        return None
    token.revoked_at = now  # eski token bekor qilinadi (rotation)
    return issue_tokens(db, user, user_agent, ip)


def revoke_token(db: Session, raw_refresh: str) -> None:
    token = db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw_refresh))
    )
    if token and not token.revoked_at:
        token.revoked_at = datetime.now(timezone.utc)
        db.commit()

def register_user(db: Session, data: RegisterRequest) -> User | None:
    if db.scalar(select(User).where(User.login == data.login)):
        return None  # login band
    role = db.scalar(select(Role).where(Role.name == "user"))
    user = User(
        login=data.login,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        role_id=role.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user        