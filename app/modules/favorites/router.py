from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.catalog.schemas import ClothesCard, PatternCard
from app.modules.favorites import service

router = APIRouter(prefix="/favorites", tags=["favorites"])


class FavoriteIds(BaseModel):
    clothes_ids: list[int]
    pattern_ids: list[int]


@router.get("", response_model=FavoriteIds)
def my_favorite_ids(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return service.favorite_ids(db, user)


@router.get("/clothes", response_model=list[ClothesCard])
def my_clothes(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return service.list_clothes(db, user)


@router.put("/clothes/{clothes_id}", status_code=status.HTTP_204_NO_CONTENT)
def add_clothes(clothes_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    service.add_clothes(db, user, clothes_id)


@router.delete("/clothes/{clothes_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_clothes(clothes_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    service.remove_clothes(db, user, clothes_id)


@router.get("/patterns", response_model=list[PatternCard])
def my_patterns(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return service.list_patterns(db, user)


@router.put("/patterns/{pattern_id}", status_code=status.HTTP_204_NO_CONTENT)
def add_pattern(pattern_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    service.add_pattern(db, user, pattern_id)


@router.delete("/patterns/{pattern_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_pattern(pattern_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    service.remove_pattern(db, user, pattern_id)