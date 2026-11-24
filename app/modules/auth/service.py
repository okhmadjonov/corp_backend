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

# Ikki tab (yoki React StrictMode) bir vaqtda refresh qilsa, ikkinchisi eski cookie
# bilan keladi. Shu vaqt ichida bunga o'g'irlik deb qaralmaydi: faqat access token
# beriladi (yangi cookie'ni brauzer birinchi javobdan allaqachon olgan).
REUSE_GRACE = timedelta(seconds=30)

ADMIN_ROLES = ("super_admin", "operator")

# (access token javobi, cookie'ga yoziladigan yangi refresh token yoki None)
Issued = tuple[TokenResponse, str | None]


def authenticate(db: Session, login: str, password: str) -> User | None:
    user = db.scalar(select(User).where(User.login == login, User.is_deleted.is_(False)))
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


def _access(user: User) -> TokenResponse:
    return TokenResponse(access_token=create_access_token(user.id, user.role.name))


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


def issue_tokens(db: Session, user: User, user_agent: str | None, ip: str | None) -> Issued:
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
    return _access(user), raw_refresh


def _active_user(db: Session, user_id: int) -> User | None:
    user = db.get(User, user_id)
    return user if user and not user.is_deleted else None


def _has_active_successor(db: Session, token: RefreshToken) -> bool:
    """Rotation'dan keyin yaratilgan token hali tirikmi (logout/parol tiklash bo'lmaganmi)."""
    return bool(db.scalar(
        select(RefreshToken.id).where(
            RefreshToken.user_id == token.user_id,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.created_at >= token.created_at,
            RefreshToken.id != token.id,
        ).limit(1)
    ))


def refresh_tokens(
    db: Session, raw_refresh: str, user_agent: str | None, ip: str | None
) -> Issued | None:
    token = db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw_refresh))
    )
    now = datetime.now(timezone.utc)
    if not token or token.expires_at <= now:
        return None

    if token.revoked_at:
        if not token.rotated_at:
            return None  # logout, parol tiklash yoki o'chirish orqali bekor qilingan
        if now - token.rotated_at <= REUSE_GRACE and _has_active_successor(db, token):
            user = _active_user(db, token.user_id)
            return (_access(user), None) if user else None
        # Almashtirilgan token kechikib qayta keldi -> ehtimol o'g'irlangan.
        revoke_all_tokens(db, token.user_id)
        db.commit()
        return None

    user = _active_user(db, token.user_id)
    if not user:
        return None
    token.revoked_at = token.rotated_at = now  # rotation
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
