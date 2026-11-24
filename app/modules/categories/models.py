from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import BaseModel


class Gender(BaseModel):
    __tablename__ = "genders"

    name: Mapped[str] = mapped_column(String(50), unique=True)


class Season(BaseModel):
    __tablename__ = "seasons"

    name: Mapped[str] = mapped_column(String(50), unique=True)


class Tag(BaseModel):
    __tablename__ = "tags"

    name: Mapped[str] = mapped_column(String(50))
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)