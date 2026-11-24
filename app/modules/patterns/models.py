from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean, Column, ForeignKey, Integer, Numeric, String, Table, Text, text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base, BaseModel

if TYPE_CHECKING:
    from app.modules.categories.models import Gender, Season, Tag
    from app.modules.clothes.models import Clothes

clothes_patterns = Table(
    "clothes_patterns",
    Base.metadata,
    Column("clothes_id", ForeignKey("clothes.id", ondelete="CASCADE"), primary_key=True),
    Column("pattern_id", ForeignKey("patterns.id", ondelete="CASCADE"), primary_key=True),
)

patterns_tags = Table(
    "patterns_tags",
    Base.metadata,
    Column("pattern_id", ForeignKey("patterns.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Pattern(BaseModel):
    __tablename__ = "patterns"

    name: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(250), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    brand: Mapped[str | None] = mapped_column(String(100))
    material: Mapped[str | None] = mapped_column(String(100))
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
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
    files: Mapped[list["PatternFile"]] = relationship(back_populates="pattern")
    tags: Mapped[list["Tag"]] = relationship(secondary=patterns_tags)
    clothes: Mapped[list["Clothes"]] = relationship(
        secondary=clothes_patterns, back_populates="patterns"
    )


class PatternFile(BaseModel):
    __tablename__ = "pattern_files"

    pattern_id: Mapped[int] = mapped_column(
        ForeignKey("patterns.id", ondelete="CASCADE"), index=True
    )
    url: Mapped[str] = mapped_column(String(500))
    kind: Mapped[str] = mapped_column(String(20))       # preview | download
    file_type: Mapped[str] = mapped_column(String(20))  # image | pdf
    sort_order: Mapped[int] = mapped_column(
        Integer, default=0, server_default=text("0")
    )
    is_main: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false")
    )

    pattern: Mapped["Pattern"] = relationship(back_populates="files")