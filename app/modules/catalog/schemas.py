from decimal import Decimal
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, field_validator

from app.modules.categories.schemas import NameOut, TagOut
from app.modules.clothes.schemas import ClothesOut
from app.modules.patterns.schemas import FileOut

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int


class ClothesCard(BaseModel):
    id: int
    name: str
    slug: str
    brand: str | None
    views_count: int
    gender: NameOut
    season: NameOut
    main_image: str | None
    min_price: Decimal | None


class PatternCard(BaseModel):
    id: int
    name: str
    slug: str
    brand: str | None
    views_count: int
    price: Decimal
    gender: NameOut
    season: NameOut
    preview_image: str | None


class ClothesDetail(ClothesOut):
    """Admin sxemasi bilan bir xil, faqat nofaol patternlar yashiriladi."""

    @field_validator("patterns", mode="before")
    @classmethod
    def _only_active_patterns(cls, items):
        return [i for i in items if not i.is_deleted and i.is_active]


class ClothesShort(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str


class PatternDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    description: str | None
    brand: str | None
    material: str | None
    price: Decimal
    views_count: int
    gender: NameOut
    season: NameOut
    tags: list[TagOut]
    files: list[FileOut]
    clothes: list[ClothesShort]

    @field_validator("tags", mode="before")
    @classmethod
    def _alive_tags(cls, items):
        return [i for i in items if not i.is_deleted]

    @field_validator("clothes", mode="before")
    @classmethod
    def _active_clothes(cls, items):
        return [i for i in items if not i.is_deleted and i.is_active]

    @field_validator("files", mode="before")
    @classmethod
    def _preview_files_only(cls, items):
        # pullik "download" fayllar hech qachon ommaga chiqmaydi
        return [i for i in items if not i.is_deleted and i.kind == "preview"]