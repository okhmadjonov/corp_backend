from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, selectinload

from app.core.crud import (
    alive_by_ids, check_exists, commit_or_409, flush_or_409, soft_delete_children,
    unique_slug,
)
from app.core.utils import like_pattern
from app.modules.categories.models import Gender, Season, Tag
from app.modules.clothes.models import Clothes
from app.modules.patterns.models import Pattern, PatternFile
from app.modules.patterns.schemas import FileIn, PatternIn

LOAD = (
    selectinload(Pattern.gender),
    selectinload(Pattern.season),
    selectinload(Pattern.tags),
    selectinload(Pattern.clothes),
    selectinload(Pattern.files),
)


def list_patterns(db: Session, limit: int, offset: int, q: str | None) -> dict:
    conds = [Pattern.is_deleted.is_(False)]
    if q:
        conds.append(Pattern.name.ilike(like_pattern(q), escape="\\"))
    total = db.scalar(select(func.count()).select_from(Pattern).where(*conds))
    rows = db.scalars(
        select(Pattern).where(*conds).options(*LOAD)
        .order_by(Pattern.id.desc()).limit(limit).offset(offset)
    ).all()
    return {"items": rows, "total": total, "limit": limit, "offset": offset}


def get_pattern(db: Session, pattern_id: int) -> Pattern:
    item = db.scalar(
        select(Pattern)
        .where(Pattern.id == pattern_id, Pattern.is_deleted.is_(False))
        .options(*LOAD)
    )
    if not item:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pattern topilmadi")
    return item


def create_pattern(db: Session, user, data: PatternIn) -> Pattern:
    check_exists(db, Gender, data.gender_id, "Gender")
    check_exists(db, Season, data.season_id, "Season")
    item = Pattern(
        **data.model_dump(exclude={"tag_ids", "clothes_ids"}),
        slug=unique_slug(db, Pattern, data.name),
        created_by=user.id,
    )
    item.tags = alive_by_ids(db, Tag, data.tag_ids, "Teg")
    item.clothes = alive_by_ids(db, Clothes, data.clothes_ids, "Kiyim")
    db.add(item)
    commit_or_409(db)
    return get_pattern(db, item.id)


def update_pattern(db: Session, user, pattern_id: int, data: PatternIn) -> Pattern:
    item = get_pattern(db, pattern_id)
    check_exists(db, Gender, data.gender_id, "Gender")
    check_exists(db, Season, data.season_id, "Season")
    for key, value in data.model_dump(exclude={"tag_ids", "clothes_ids"}).items():
        setattr(item, key, value)
    item.tags = alive_by_ids(db, Tag, data.tag_ids, "Teg")
    item.clothes = alive_by_ids(db, Clothes, data.clothes_ids, "Kiyim")
    item.updated_by = user.id
    commit_or_409(db)
    return get_pattern(db, pattern_id)


def delete_pattern(db: Session, user, pattern_id: int) -> None:
    item = get_pattern(db, pattern_id)
    item.is_deleted = True
    item.deleted_at = datetime.now(timezone.utc)
    item.deleted_by = user.id
    soft_delete_children(db, PatternFile.pattern_id, pattern_id, user)
    commit_or_409(db)


# ---- fayllar ----

def get_file(db: Session, pattern_id: int, file_id: int) -> PatternFile:
    f = db.get(PatternFile, file_id)
    if not f or f.is_deleted or f.pattern_id != pattern_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Fayl topilmadi")
    return f


def _keep_single_main(db: Session, pattern_id: int, keep_id: int) -> None:
    db.execute(
        update(PatternFile)
        .where(PatternFile.pattern_id == pattern_id, PatternFile.id != keep_id)
        .values(is_main=False)
    )


def add_file(db: Session, user, pattern_id: int, data: FileIn) -> PatternFile:
    get_pattern(db, pattern_id)
    f = PatternFile(pattern_id=pattern_id, created_by=user.id, **data.model_dump())
    db.add(f)
    flush_or_409(db)
    if data.is_main:
        _keep_single_main(db, pattern_id, f.id)
    commit_or_409(db)
    db.refresh(f)
    return f


def update_file(db: Session, user, pattern_id: int, file_id: int, data: FileIn) -> PatternFile:
    f = get_file(db, pattern_id, file_id)
    for key, value in data.model_dump().items():
        setattr(f, key, value)
    f.updated_by = user.id
    if data.is_main:
        _keep_single_main(db, pattern_id, f.id)
    commit_or_409(db)
    db.refresh(f)
    return f


def delete_file(db: Session, user, pattern_id: int, file_id: int) -> None:
    f = get_file(db, pattern_id, file_id)
    f.is_deleted = True
    f.deleted_at = datetime.now(timezone.utc)
    f.deleted_by = user.id
    commit_or_409(db)