from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.dependencies import require_roles
from app.modules.catalog.schemas import Page
from app.modules.users import service
from app.modules.users.schemas import (
    AdminUserOut, PasswordReset, RoleName, UserCreate, UserUpdate,
)

router = APIRouter(prefix="/admin/users", tags=["admin: users"])

super_admin_only = require_roles("super_admin")


@router.get("", response_model=Page[AdminUserOut])
def list_users(
    role: RoleName | None = None,
    q: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    actor=Depends(super_admin_only),
):
    return service.list_users(db, role, q, limit, offset)


@router.post("", response_model=AdminUserOut, status_code=status.HTTP_201_CREATED)
def create_user(data: UserCreate, db: Session = Depends(get_db), actor=Depends(super_admin_only)):
    return service.create_user(db, actor, data)


@router.get("/{user_id}", response_model=AdminUserOut)
def get_user(user_id: int, db: Session = Depends(get_db), actor=Depends(super_admin_only)):
    return service.get_user(db, user_id)


@router.put("/{user_id}", response_model=AdminUserOut)
def update_user(
    user_id: int, data: UserUpdate, db: Session = Depends(get_db), actor=Depends(super_admin_only)
):
    return service.update_user(db, actor, user_id, data)


@router.post("/{user_id}/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(
    user_id: int, data: PasswordReset, db: Session = Depends(get_db), actor=Depends(super_admin_only)
):
    service.reset_password(db, actor, user_id, data)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db), actor=Depends(super_admin_only)):
    service.delete_user(db, actor, user_id)