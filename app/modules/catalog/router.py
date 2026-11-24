from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.schemas import Page
from app.modules.auth.dependencies import get_current_user
from app.modules.catalog import service
from app.modules.catalog.schemas import (
    ClothesCard, ClothesDetail, PatternCard, PatternDetail,
)

router = APIRouter(tags=["catalog"])

Sort = Literal["new", "popular"]


@router.get("/clothes", response_model=Page[ClothesCard])
def list_clothes(
    gender_id: int | None = None,
    season_id: int | None = None,
    q: str | None = None,
    tag: str | None = Query(None, description="teg slug"),
    sort: Sort = "new",
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return service.list_clothes(db, gender_id, season_id, q, tag, sort, limit, offset)


@router.get("/clothes/{slug}", response_model=ClothesDetail)
def clothes_detail(slug: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return service.clothes_detail(db, slug)


@router.get("/patterns", response_model=Page[PatternCard])
def list_patterns(
    gender_id: int | None = None,
    season_id: int | None = None,
    q: str | None = None,
    tag: str | None = Query(None, description="teg slug"),
    sort: Sort = "new",
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return service.list_patterns(db, gender_id, season_id, q, tag, sort, limit, offset)


@router.get("/patterns/{slug}", response_model=PatternDetail)
def pattern_detail(slug: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return service.pattern_detail(db, slug)