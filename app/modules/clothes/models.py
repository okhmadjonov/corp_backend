from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean, Column, ForeignKey, Integer, Numeric, String, Table, Text, text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base, BaseModel
if TYPE_CHECKING:
    from app.modules.categories.models import Gender, Season, Tag
    
clothes_tags = Table(
    "clothes_tags",
    Base.metadata,
    Column("clothes_id", ForeignKey("clothes.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Clothes(BaseModel):
    __tablename__ = "clothes"

    name: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(250), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    brand: Mapped[str | None] = mapped_column(String(100))
    material: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=text("true")
    )
    views_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default=text("0")
    )
    gender_id: Mapped[int] = mapped_column(ForeignKey("genders.id"), index=True)
    season_id: Mapped[int] = mapped_column(ForeignKey("seasons.id"), index=True)

    gender: Mapped["Gender"] = relationship()
    season: Mapped["Season"] = relationship()
    variants: Mapped[list["ClothingVariant"]] = relationship(back_populates="clothes")
    images: Mapped[list["ClothesImage"]] = relationship(back_populates="clothes")
    tags: Mapped[list["Tag"]] = relationship(secondary=clothes_tags)


class ClothingVariant(BaseModel):
    __tablename__ = "clothing_variants"

    clothes_id: Mapped[int] = mapped_column(
        ForeignKey("clothes.id", ondelete="CASCADE"), index=True
    )
    size: Mapped[str] = mapped_column(String(20))
    color: Mapped[str] = mapped_column(String(50))
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    stock_quantity: Mapped[int] = mapped_column(
        Integer, default=0, server_default=text("0")
    )
    sku: Mapped[str] = mapped_column(String(64), unique=True)

    clothes: Mapped["Clothes"] = relationship(back_populates="variants")


class ClothesImage(BaseModel):
    __tablename__ = "clothes_images"

    clothes_id: Mapped[int] = mapped_column(
        ForeignKey("clothes.id", ondelete="CASCADE"), index=True
    )
    url: Mapped[str] = mapped_column(String(500))
    sort_order: Mapped[int] = mapped_column(
        Integer, default=0, server_default=text("0")
    )
    is_main: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false")
    )

    clothes: Mapped["Clothes"] = relationship(back_populates="images")