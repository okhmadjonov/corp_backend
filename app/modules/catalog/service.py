from fastapi import HTTPException, status
from sqlalchemy import and_, func, select, update
from sqlalchemy.orm import Session, selectinload

from app.core.utils import like_pattern
from app.modules.categories.models import Tag
from app.modules.clothes.models import Clothes
from app.modules.clothes.service import LOAD as CLOTHES_LOAD
from app.modules.patterns.models import Pattern
from app.modules.patterns.service import LOAD as PATTERN_LOAD


def _filters(model, gender_id, season_id, q, tag):
    conds = [model.is_deleted.is_(False), model.is_active.is_(True)]
    if gender_id:
        conds.append(model.gender_id == gender_id)
    if season_id:
        conds.append(model.season_id == season_id)
    if q:
        conds.append(model.name.ilike(like_pattern(q), escape="\\"))
    if tag:
        conds.append(model.tags.any(and_(Tag.slug == tag, Tag.is_deleted.is_(False))))
    return conds


def _order(model, sort: str):
    if sort == "popular":
        return (model.views_count.desc(), model.id.desc())
    return (model.id.desc(),)


def _sorted_images(items):
    alive = [i for i in items if not i.is_deleted]
    return sorted(alive, key=lambda i: (not i.is_main, i.sort_order, i.id))


def _clothes_card(c: Clothes) -> dict:
    images = _sorted_images(c.images)
    prices = [v.price for v in c.variants if not v.is_deleted]
    return {
        "id": c.id, "name": c.name, "slug": c.slug, "brand": c.brand,
        "views_count": c.views_count, "gender": c.gender, "season": c.season,
        "main_image": images[0].url if images else None,
        "min_price": min(prices) if prices else None,
    }


def _pattern_card(p: Pattern) -> dict:
    previews = [f for f in p.files if f.kind == "preview" and f.file_type == "image"]
    previews = _sorted_images(previews)
    return {
        "id": p.id, "name": p.name, "slug": p.slug, "brand": p.brand,
        "views_count": p.views_count, "price": p.price,
        "gender": p.gender, "season": p.season,
        "preview_image": previews[0].url if previews else None,
    }


def list_clothes(db: Session, gender_id, season_id, q, tag, sort, limit, offset) -> dict:
    conds = _filters(Clothes, gender_id, season_id, q, tag)
    total = db.scalar(select(func.count()).select_from(Clothes).where(*conds))
    rows = db.scalars(
        select(Clothes)
        .where(*conds)
        .options(
            selectinload(Clothes.gender), selectinload(Clothes.season),
            selectinload(Clothes.variants), selectinload(Clothes.images),
        )
        .order_by(*_order(Clothes, sort))
        .limit(limit).offset(offset)
    ).all()
    return {"items": [_clothes_card(c) for c in rows], "total": total,
            "limit": limit, "offset": offset}


def list_patterns(db: Session, gender_id, season_id, q, tag, sort, limit, offset) -> dict:
    conds = _filters(Pattern, gender_id, season_id, q, tag)
    total = db.scalar(select(func.count()).select_from(Pattern).where(*conds))
    rows = db.scalars(
        select(Pattern)
        .where(*conds)
        .options(
            selectinload(Pattern.gender), selectinload(Pattern.season),
            selectinload(Pattern.files),
        )
        .order_by(*_order(Pattern, sort))
        .limit(limit).offset(offset)
    ).all()
    return {"items": [_pattern_card(p) for p in rows], "total": total,
            "limit": limit, "offset": offset}


def _detail(db: Session, model, load, slug: str, label: str):
    item_id = db.scalar(
        select(model.id).where(
            model.slug == slug, model.is_deleted.is_(False), model.is_active.is_(True)
        )
    )
    if not item_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"{label} topilmadi")
    db.execute(
        update(model).where(model.id == item_id)
        .values(views_count=model.views_count + 1)
    )
    db.commit()
    return db.scalar(select(model).where(model.id == item_id).options(*load))


def clothes_detail(db: Session, slug: str):
    return _detail(db, Clothes, CLOTHES_LOAD, slug, "Kiyim")


def pattern_detail(db: Session, slug: str):
    return _detail(db, Pattern, PATTERN_LOAD, slug, "Pattern")