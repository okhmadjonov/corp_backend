from app.core.utils import slugify
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


def _commit(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Bunday qiymat allaqachon mavjud")


def list_items(db: Session, model):
    stmt = select(model).where(model.is_deleted.is_(False)).order_by(model.id)
    return db.scalars(stmt).all()


def get_or_404(db: Session, model, item_id: int):
    item = db.get(model, item_id)
    if not item or item.is_deleted:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Topilmadi")
    return item


def create_item(db: Session, model, user, data: dict):
    item = model(**data, created_by=user.id)
    db.add(item)
    _commit(db)
    db.refresh(item)
    return item


def update_item(db: Session, model, item_id: int, user, data: dict):
    item = get_or_404(db, model, item_id)
    for key, value in data.items():
        setattr(item, key, value)
    item.updated_by = user.id
    _commit(db)
    db.refresh(item)
    return item


def soft_delete_item(db: Session, model, item_id: int, user) -> None:
    item = get_or_404(db, model, item_id)
    item.is_deleted = True
    item.deleted_at = datetime.now(timezone.utc)
    item.deleted_by = user.id
    _commit(db)

commit_or_409 = _commit


def flush_or_409(db: Session) -> None:
    """flush ham UNIQUE xatosini berishi mumkin (masalan, takroriy SKU) -> 409."""
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Bunday qiymat allaqachon mavjud")


def soft_delete_children(db: Session, fk_column, parent_id: int, user) -> None:
    """Ota-yozuv o'chirilganda bolalarini ham soft-delete qiladi
    (aks holda masalan SKU o'chirilgan kiyimning variantida band qolib ketadi)."""
    model = fk_column.class_
    db.execute(
        update(model)
        .where(fk_column == parent_id, model.is_deleted.is_(False))
        .values(is_deleted=True, deleted_at=datetime.now(timezone.utc), deleted_by=user.id)
    )


def unique_slug(db: Session, model, text: str) -> str:
    base = slugify(text) or "item"
    slug, n = base, 2
    while db.scalar(
        select(model.id).where(model.slug == slug, model.is_deleted.is_(False))
    ):
        slug = f"{base}-{n}"
        n += 1
    return slug    

def check_exists(db: Session, model, item_id: int, label: str) -> None:
    found = db.scalar(
        select(model.id).where(model.id == item_id, model.is_deleted.is_(False))
    )
    if not found:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"{label} topilmadi")


def alive_by_ids(db: Session, model, ids: list[int], label: str) -> list:
    ids = list(dict.fromkeys(ids))
    if not ids:
        return []
    rows = db.scalars(
        select(model).where(model.id.in_(ids), model.is_deleted.is_(False))
    ).all()
    if len(rows) != len(ids):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"{label} topilmadi")
    return list(rows)    