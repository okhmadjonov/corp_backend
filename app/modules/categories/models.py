from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import BaseModel, unique_alive


class Gender(BaseModel):
    __tablename__ = "genders"
    __table_args__ = (unique_alive("genders", "name"),)

    name: Mapped[str] = mapped_column(String(50))


class Season(BaseModel):
    __tablename__ = "seasons"
    __table_args__ = (unique_alive("seasons", "name"),)

    name: Mapped[str] = mapped_column(String(50))


class Tag(BaseModel):
    __tablename__ = "tags"
    __table_args__ = (unique_alive("tags", "name"), unique_alive("tags", "slug"))

    name: Mapped[str] = mapped_column(String(50))
    slug: Mapped[str] = mapped_column(String(80))
