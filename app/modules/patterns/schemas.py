from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.categories.schemas import NameOut, TagOut


class PatternIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    brand: str | None = Field(default=None, max_length=100)
    material: str | None = Field(default=None, max_length=100)
    price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    is_active: bool = True
    gender_id: int
    season_id: int
    tag_ids: list[int] = []
    clothes_ids: list[int] = []


class FileIn(BaseModel):
    url: str = Field(min_length=1, max_length=500)
    kind: Literal["preview", "download"]
    file_type: Literal["image", "pdf"]
    sort_order: int = 0
    is_main: bool = False


class FileOut(FileIn):
    model_config = ConfigDict(from_attributes=True)

    id: int


class ClothesBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str


class PatternOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    description: str | None
    brand: str | None
    material: str | None
    price: Decimal
    is_active: bool
    views_count: int
    created_at: datetime
    gender: NameOut
    season: NameOut
    tags: list[TagOut]
    files: list[FileOut]
    clothes: list[ClothesBrief]

    @field_validator("tags", "files", "clothes", mode="before")
    @classmethod
    def _hide_deleted(cls, items):
        return [i for i in items if not i.is_deleted]