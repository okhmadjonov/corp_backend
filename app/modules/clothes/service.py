from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, selectinload

from app.core.crud import (
    alive_by_ids as _alive_by_ids,
    check_exists as _check_exists,
    commit_or_409,
    unique_slug,
)
from app.core.utils import like_pattern
from app.modules.categories.models import Gender, Season, Tag
from app.modules.clothes.models import Clothes, ClothesImage
from app.modules.clothes.schemas import ClothesIn
from app.modules.patterns.models import Pattern

LOAD = (
    selectinload(Clothes.gender),
    selectinload(Clothes.season),
    selectinload(Clothes.tags),
    selectinload(Clothes.patterns),
    selectinload(Clothes.variants),
    selectinload(Clothes.images),
)




def list_clothes(db: Session, limit: int, offset: int, q: str | None) -> dict:
    conds = [Clothes.is_deleted.is_(False)]
    if q:
        conds.append(Clothes.name.ilike(like_pattern(q), escape="\\"))
    total = db.scalar(select(func.count()).select_from(Clothes).where(*conds))
    rows = db.scalars(
        select(Clothes).where(*conds).options(*LOAD)
        .order_by(Clothes.id.desc()).limit(limit).offset(offset)
    ).all()
    return {"items": rows, "total": total, "limit": limit, "offset": offset}


def get_clothes(db: Session, clothes_id: int) -> Clothes:
    item = db.scalar(
        select(Clothes)
        .where(Clothes.id == clothes_id, Clothes.is_deleted.is_(False))
        .options(*LOAD)
    )
    if not item:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kiyim topilmadi")
    return item


def create_clothes(db: Session, user, data: ClothesIn) -> Clothes:
    _check_exists(db, Gender, data.gender_id, "Gender")
    _check_exists(db, Season, data.season_id, "Season")
    item = Clothes(
        **data.model_dump(exclude={"tag_ids", "pattern_ids"}),
        slug=unique_slug(db, Clothes, data.name),
        created_by=user.id,
    )
    item.tags = _alive_by_ids(db, Tag, data.tag_ids, "Teg")
    item.patterns = _alive_by_ids(db, Pattern, data.pattern_ids, "Pattern")
    db.add(item)
    commit_or_409(db)
    return get_clothes(db, item.id)


def update_clothes(db: Session, user, clothes_id: int, data: ClothesIn) -> Clothes:
    item = get_clothes(db, clothes_id)
    _check_exists(db, Gender, data.gender_id, "Gender")
    _check_exists(db, Season, data.season_id, "Season")
    for key, value in data.model_dump(exclude={"tag_ids", "pattern_ids"}).items():
        setattr(item, key, value)  # slug o'zgarmaydi (URL barqaror qoladi)
    item.tags = _alive_by_ids(db, Tag, data.tag_ids, "Teg")
    item.patterns = _alive_by_ids(db, Pattern, data.pattern_ids, "Pattern")
    item.updated_by = user.id
    commit_or_409(db)
    return get_clothes(db, clothes_id)


def delete_clothes(db: Session, user, clothes_id: int) -> None:
    item = get_clothes(db, clothes_id)
    item.is_deleted = True
    item.deleted_at = datetime.now(timezone.utc)
    item.deleted_by = user.id
    commit_or_409(db)


# ---- variant va rasm uchun umumiy funksiyalar ----

def _get_child(db: Session, model, clothes_id: int, child_id: int):
    child = db.get(model, child_id)
    if not child or child.is_deleted or child.clothes_id != clothes_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Topilmadi")
    return child


def _keep_single_main(db: Session, clothes_id: int, keep_id: int) -> None:
    db.execute(
        update(ClothesImage)
        .where(ClothesImage.clothes_id == clothes_id, ClothesImage.id != keep_id)
        .values(is_main=False)
    )


def add_child(db: Session, user, clothes_id: int, model, data):
    get_clothes(db, clothes_id)  # kiyim bormi, tekshiradi
    values = data.model_dump()
    child = model(clothes_id=clothes_id, created_by=user.id, **values)
    db.add(child)
    db.flush()
    if values.get("is_main"):
        _keep_single_main(db, clothes_id, child.id)
    commit_or_409(db)
    db.refresh(child)
    return child


def update_child(db: Session, user, clothes_id: int, child_id: int, model, data):
    child = _get_child(db, model, clothes_id, child_id)
    values = data.model_dump()
    for key, value in values.items():
        setattr(child, key, value)
    child.updated_by = user.id
    if values.get("is_main"):
        _keep_single_main(db, clothes_id, child.id)
    commit_or_409(db)
    db.refresh(child)
    return child


def delete_child(db: Session, user, clothes_id: int, child_id: int, model) -> None:
    child = _get_child(db, model, clothes_id, child_id)
    child.is_deleted = True
    child.deleted_at = datetime.now(timezone.utc)
    child.deleted_by = user.id
    commit_or_409(db)