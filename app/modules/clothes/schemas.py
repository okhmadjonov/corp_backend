from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.categories.schemas import NameOut, TagOut


class ClothesIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    brand: str | None = Field(default=None, max_length=100)
    material: str | None = Field(default=None, max_length=100)
    is_active: bool = True
    gender_id: int
    season_id: int
    tag_ids: list[int] = []
    pattern_ids: list[int] = []


class VariantIn(BaseModel):
    size: str = Field(min_length=1, max_length=20)
    color: str = Field(min_length=1, max_length=50)
    price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    stock_quantity: int = Field(default=0, ge=0)
    sku: str = Field(min_length=1, max_length=64)


class VariantOut(VariantIn):
    model_config = ConfigDict(from_attributes=True)

    id: int


class ImageIn(BaseModel):
    url: str = Field(min_length=1, max_length=500)
    sort_order: int = 0
    is_main: bool = False


class ImageOut(ImageIn):
    model_config = ConfigDict(from_attributes=True)

    id: int


class PatternBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str


class ClothesOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    description: str | None
    brand: str | None
    material: str | None
    is_active: bool
    views_count: int
    created_at: datetime
    gender: NameOut
    season: NameOut
    tags: list[TagOut]
    variants: list[VariantOut]
    images: list[ImageOut]
    patterns: list[PatternBrief]

    @field_validator("tags", "variants", "images", "patterns", mode="before")
    @classmethod
    def _hide_deleted(cls, items):
        return [i for i in items if not i.is_deleted]