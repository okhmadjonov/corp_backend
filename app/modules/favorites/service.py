from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session, selectinload

from app.modules.catalog.service import _clothes_card, _pattern_card
from app.modules.clothes.models import Clothes
from app.modules.favorites.models import favorite_clothes, favorite_patterns
from app.modules.patterns.models import Pattern


def favorite_ids(db: Session, user) -> dict:
    return {
        "clothes_ids": list(db.scalars(
            select(favorite_clothes.c.clothes_id)
            .where(favorite_clothes.c.user_id == user.id)
        )),
        "pattern_ids": list(db.scalars(
            select(favorite_patterns.c.pattern_id)
            .where(favorite_patterns.c.user_id == user.id)
        )),
    }


def list_clothes(db: Session, user) -> list[dict]:
    rows = db.scalars(
        select(Clothes)
        .join(favorite_clothes, favorite_clothes.c.clothes_id == Clothes.id)
        .where(
            favorite_clothes.c.user_id == user.id,
            Clothes.is_deleted.is_(False),
            Clothes.is_active.is_(True),
        )
        .options(
            selectinload(Clothes.gender), selectinload(Clothes.season),
            selectinload(Clothes.variants), selectinload(Clothes.images),
        )
        .order_by(favorite_clothes.c.created_at.desc())
    ).all()
    return [_clothes_card(c) for c in rows]


def list_patterns(db: Session, user) -> list[dict]:
    rows = db.scalars(
        select(Pattern)
        .join(favorite_patterns, favorite_patterns.c.pattern_id == Pattern.id)
        .where(
            favorite_patterns.c.user_id == user.id,
            Pattern.is_deleted.is_(False),
            Pattern.is_active.is_(True),
        )
        .options(
            selectinload(Pattern.gender), selectinload(Pattern.season),
            selectinload(Pattern.files),
        )
        .order_by(favorite_patterns.c.created_at.desc())
    ).all()
    return [_pattern_card(p) for p in rows]


def _ensure_active(db: Session, model, item_id: int) -> None:
    found = db.scalar(
        select(model.id).where(
            model.id == item_id, model.is_deleted.is_(False), model.is_active.is_(True)
        )
    )
    if not found:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Topilmadi")


def add_clothes(db: Session, user, clothes_id: int) -> None:
    _ensure_active(db, Clothes, clothes_id)
    db.execute(
        insert(favorite_clothes)
        .values(user_id=user.id, clothes_id=clothes_id)
        .on_conflict_do_nothing()
    )
    db.commit()


def remove_clothes(db: Session, user, clothes_id: int) -> None:
    db.execute(
        delete(favorite_clothes).where(
            favorite_clothes.c.user_id == user.id,
            favorite_clothes.c.clothes_id == clothes_id,
        )
    )
    db.commit()


def add_pattern(db: Session, user, pattern_id: int) -> None:
    _ensure_active(db, Pattern, pattern_id)
    db.execute(
        insert(favorite_patterns)
        .values(user_id=user.id, pattern_id=pattern_id)
        .on_conflict_do_nothing()
    )
    db.commit()


def remove_pattern(db: Session, user, pattern_id: int) -> None:
    db.execute(
        delete(favorite_patterns).where(
            favorite_patterns.c.user_id == user.id,
            favorite_patterns.c.pattern_id == pattern_id,
        )
    )
    db.commit()