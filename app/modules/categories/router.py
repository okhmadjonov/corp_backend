from typing import Callable

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core import crud
from app.core.database import get_db
from app.modules.auth.dependencies import admin_only
from app.modules.categories import service
from app.modules.categories.models import Gender, Season, Tag
from app.modules.categories.schemas import NameIn, NameOut, TagOut


def _dump(_db: Session, data) -> dict:
    return data.model_dump()


def make_crud_router(
    prefix: str,
    model,
    schema_in,
    schema_out,
    prepare_create: Callable[[Session, object], dict] = _dump,
    prepare_update: Callable[[Session, object], dict] = _dump,
    ensure_unused: Callable[[Session, int], None] | None = None,
) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=[prefix.strip("/")])

    @router.get("", response_model=list[schema_out])
    def list_all(db: Session = Depends(get_db)):
        return crud.list_items(db, model)

    @router.get("/{item_id}", response_model=schema_out)
    def get_one(item_id: int, db: Session = Depends(get_db)):
        return crud.get_or_404(db, model, item_id)

    @router.post("", response_model=schema_out, status_code=status.HTTP_201_CREATED)
    def create(data: schema_in, db: Session = Depends(get_db), user=Depends(admin_only)):
        return crud.create_item(db, model, user, prepare_create(db, data))

    @router.put("/{item_id}", response_model=schema_out)
    def update(
        item_id: int, data: schema_in, db: Session = Depends(get_db), user=Depends(admin_only)
    ):
        return crud.update_item(db, model, item_id, user, prepare_update(db, data))

    @router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete(item_id: int, db: Session = Depends(get_db), user=Depends(admin_only)):
        crud.get_or_404(db, model, item_id)  # avval 404, keyin 409
        if ensure_unused:
            ensure_unused(db, item_id)  # ishlatilayotgan bo'lsa 409
        crud.soft_delete_item(db, model, item_id, user)

    return router


router = APIRouter()
router.include_router(
    make_crud_router(
        "/genders", Gender, NameIn, NameOut, ensure_unused=service.ensure_gender_unused
    )
)
router.include_router(
    make_crud_router(
        "/seasons", Season, NameIn, NameOut, ensure_unused=service.ensure_season_unused
    )
)
router.include_router(
    make_crud_router(
        "/tags",
        Tag,
        NameIn,
        TagOut,
        # slug faqat yaratishda beriladi: nom o'zgarsa ham ?tag=... havolalari buzilmaydi
        prepare_create=lambda db, d: {"name": d.name, "slug": crud.unique_slug(db, Tag, d.name)},
        prepare_update=lambda db, d: {"name": d.name},
        ensure_unused=service.ensure_tag_unused,
    )
)