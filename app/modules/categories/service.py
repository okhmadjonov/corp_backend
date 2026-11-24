"""Kategoriya o'chirilishidan oldin u ishlatilayotganini tekshirish."""
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.clothes.models import Clothes, clothes_tags
from app.modules.patterns.models import Pattern, patterns_tags


def _alive_count(db: Session, model, *conds) -> int:
    return db.scalar(
        select(func.count()).select_from(model).where(model.is_deleted.is_(False), *conds)
    )


def _raise_if_used(clothes: int, patterns: int) -> None:
    if clothes or patterns:
        parts = []
        if clothes:
            parts.append(f"{clothes} ta kiyim")
        if patterns:
            parts.append(f"{patterns} ta pattern")
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"O'chirib bo'lmaydi: {' va '.join(parts)}da ishlatilmoqda. "
            "Avval ularni o'zgartiring yoki o'chiring",
        )


def ensure_gender_unused(db: Session, item_id: int) -> None:
    _raise_if_used(
        _alive_count(db, Clothes, Clothes.gender_id == item_id),
        _alive_count(db, Pattern, Pattern.gender_id == item_id),
    )


def ensure_season_unused(db: Session, item_id: int) -> None:
    _raise_if_used(
        _alive_count(db, Clothes, Clothes.season_id == item_id),
        _alive_count(db, Pattern, Pattern.season_id == item_id),
    )


def ensure_tag_unused(db: Session, item_id: int) -> None:
    _raise_if_used(
        _alive_count(
            db, Clothes,
            Clothes.id.in_(select(clothes_tags.c.clothes_id).where(clothes_tags.c.tag_id == item_id)),
        ),
        _alive_count(
            db, Pattern,
            Pattern.id.in_(select(patterns_tags.c.pattern_id).where(patterns_tags.c.tag_id == item_id)),
        ),
    )
