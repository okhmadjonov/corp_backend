from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.modules.auth.models import RefreshToken, Role, User
from app.modules.auth.schemas import RegisterRequest, TokenResponse

# Bir nechta tab bir vaqtda refresh qilsa, eski token shu vaqt ichida
# qayta kelishi normal holat — o'g'irlik deb hisoblanmaydi.
REUSE_GRACE = timedelta(seconds=30)


def authenticate(db: Session, login: str, password: str) -> User | None:
    user = db.scalar(select(User).where(User.login == login, User.is_deleted.is_(False)))
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


def _cleanup_expired(db: Session, user_id: int, now: datetime) -> None:
    db.execute(
        delete(RefreshToken).where(
            RefreshToken.user_id == user_id, RefreshToken.expires_at <= now
        )
    )


def revoke_all_tokens(db: Session, user_id: int) -> None:
    db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=datetime.now(timezone.utc))
    )


def issue_tokens(
    db: Session, user: User, user_agent: str | None, ip: str | None
) -> TokenResponse:
    now = datetime.now(timezone.utc)
    _cleanup_expired(db, user.id, now)
    raw_refresh = generate_refresh_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_token(raw_refresh),
            expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
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
    if not token or token.expires_at <= now:
        return None
    if token.revoked_at:
        # Bekor qilingan token qayta ishlatildi -> ehtimol o'g'irlangan.
        # Xavfsizlik uchun foydalanuvchining barcha sessiyalari yopiladi.
        if now - token.revoked_at > REUSE_GRACE:
            revoke_all_tokens(db, token.user_id)
            db.commit()
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
    """Login band bo'lsa None qaytaradi."""
    if db.scalar(select(User.id).where(User.login == data.login, User.is_deleted.is_(False))):
        return None
    role = db.scalar(select(Role).where(Role.name == "user", Role.is_deleted.is_(False)))
    user = User(
        login=data.login,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        role_id=role.id,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:  # bir vaqtda ikki so'rov bir xil login bilan kelsa
        db.rollback()
        return None
    db.refresh(user)
    return user
