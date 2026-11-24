from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.dependencies import admin_only
from app.modules.clothes import service
from app.modules.clothes.models import ClothesImage, ClothingVariant
from app.modules.clothes.schemas import (
    ClothesIn, ClothesOut, ImageIn, ImageOut, VariantIn, VariantOut,
)

router = APIRouter(prefix="/admin/clothes", tags=["admin: clothes"])


@router.get("", response_model=list[ClothesOut])
def list_clothes(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    q: str | None = None,
    db: Session = Depends(get_db),
    user=Depends(admin_only),
):
    return service.list_clothes(db, limit, offset, q)


@router.post("", response_model=ClothesOut, status_code=status.HTTP_201_CREATED)
def create_clothes(data: ClothesIn, db: Session = Depends(get_db), user=Depends(admin_only)):
    return service.create_clothes(db, user, data)


@router.get("/{clothes_id}", response_model=ClothesOut)
def get_clothes(clothes_id: int, db: Session = Depends(get_db), user=Depends(admin_only)):
    return service.get_clothes(db, clothes_id)


@router.put("/{clothes_id}", response_model=ClothesOut)
def update_clothes(
    clothes_id: int, data: ClothesIn, db: Session = Depends(get_db), user=Depends(admin_only)
):
    return service.update_clothes(db, user, clothes_id, data)


@router.delete("/{clothes_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_clothes(clothes_id: int, db: Session = Depends(get_db), user=Depends(admin_only)):
    service.delete_clothes(db, user, clothes_id)


# ---- variantlar ----

@router.post(
    "/{clothes_id}/variants", response_model=VariantOut, status_code=status.HTTP_201_CREATED
)
def add_variant(
    clothes_id: int, data: VariantIn, db: Session = Depends(get_db), user=Depends(admin_only)
):
    return service.add_child(db, user, clothes_id, ClothingVariant, data)


@router.put("/{clothes_id}/variants/{variant_id}", response_model=VariantOut)
def update_variant(
    clothes_id: int,
    variant_id: int,
    data: VariantIn,
    db: Session = Depends(get_db),
    user=Depends(admin_only),
):
    return service.update_child(db, user, clothes_id, variant_id, ClothingVariant, data)


@router.delete("/{clothes_id}/variants/{variant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_variant(
    clothes_id: int, variant_id: int, db: Session = Depends(get_db), user=Depends(admin_only)
):
    service.delete_child(db, user, clothes_id, variant_id, ClothingVariant)


# ---- rasmlar ----

@router.post(
    "/{clothes_id}/images", response_model=ImageOut, status_code=status.HTTP_201_CREATED
)
def add_image(
    clothes_id: int, data: ImageIn, db: Session = Depends(get_db), user=Depends(admin_only)
):
    return service.add_child(db, user, clothes_id, ClothesImage, data)


@router.put("/{clothes_id}/images/{image_id}", response_model=ImageOut)
def update_image(
    clothes_id: int,
    image_id: int,
    data: ImageIn,
    db: Session = Depends(get_db),
    user=Depends(admin_only),
):
    return service.update_child(db, user, clothes_id, image_id, ClothesImage, data)


@router.delete("/{clothes_id}/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_image(
    clothes_id: int, image_id: int, db: Session = Depends(get_db), user=Depends(admin_only)
):
    service.delete_child(db, user, clothes_id, image_id, ClothesImage)