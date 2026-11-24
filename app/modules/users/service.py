from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.crud import commit_or_409
from app.core.security import hash_password
from app.core.utils import like_pattern
from app.modules.auth.models import Role, User
from app.modules.auth.service import revoke_all_tokens
from app.modules.users.schemas import PasswordReset, UserCreate, UserUpdate


def _role(db: Session, name: str) -> Role:
    role = db.scalar(select(Role).where(Role.name == name, Role.is_deleted.is_(False)))
    if not role:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Rol topilmadi")
    return role


def get_user(db: Session, user_id: int) -> User:
    user = db.scalar(
        select(User)
        .where(User.id == user_id, User.is_deleted.is_(False))
        .options(selectinload(User.role))
    )
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Foydalanuvchi topilmadi")
    return user


def _super_admin_count(db: Session) -> int:
    return db.scalar(
        select(func.count())
        .select_from(User)
        .join(Role, User.role_id == Role.id)
        .where(Role.name == "super_admin", User.is_deleted.is_(False))
    )


def list_users(db: Session, role: str | None, q: str | None, limit: int, offset: int) -> dict:
    conds = [User.is_deleted.is_(False)]
    if q:
        pattern = like_pattern(q)
        conds.append(
            User.login.ilike(pattern, escape="\\") | User.full_name.ilike(pattern, escape="\\")
        )

    base = select(User).join(Role, User.role_id == Role.id).where(*conds)
    count = select(func.count()).select_from(User).join(Role, User.role_id == Role.id).where(*conds)
    if role:
        base = base.where(Role.name == role)
        count = count.where(Role.name == role)

    total = db.scalar(count)
    rows = db.scalars(
        base.options(selectinload(User.role))
        .order_by(User.id.desc()).limit(limit).offset(offset)
    ).all()
    return {"items": rows, "total": total, "limit": limit, "offset": offset}


def create_user(db: Session, actor: User, data: UserCreate) -> User:
    if db.scalar(select(User.id).where(User.login == data.login, User.is_deleted.is_(False))):
        raise HTTPException(status.HTTP_409_CONFLICT, "Bu login band")
    user = User(
        login=data.login,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        role_id=_role(db, data.role).id,
        created_by=actor.id,
    )
    db.add(user)
    commit_or_409(db)
    return get_user(db, user.id)


def update_user(db: Session, actor: User, user_id: int, data: UserUpdate) -> User:
    user = get_user(db, user_id)
    if data.role != user.role.name:
        if user.id == actor.id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "O'z rolingizni o'zgartira olmaysiz")
        if user.role.name == "super_admin" and _super_admin_count(db) <= 1:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Oxirgi super adminning rolini o'zgartirib bo'lmaydi")
        user.role = _role(db, data.role)
    user.full_name = data.full_name
    user.updated_by = actor.id
    commit_or_409(db)
    return get_user(db, user_id)


def reset_password(db: Session, actor: User, user_id: int, data: PasswordReset) -> None:
    user = get_user(db, user_id)
    user.password_hash = hash_password(data.password)
    user.updated_by = actor.id
    revoke_all_tokens(db, user.id)  # eski sessiyalar tugatiladi
    commit_or_409(db)


def delete_user(db: Session, actor: User, user_id: int) -> None:
    user = get_user(db, user_id)
    if user.id == actor.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "O'zingizni o'chira olmaysiz")
    if user.role.name == "super_admin" and _super_admin_count(db) <= 1:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Oxirgi super adminni o'chirib bo'lmaydi")
    user.is_deleted = True
    user.deleted_at = datetime.now(timezone.utc)
    user.deleted_by = actor.id
    revoke_all_tokens(db, user.id)
    commit_or_409(db)