from sqlalchemy import Column, DateTime, ForeignKey, Table, func

from app.core.base import Base

favorite_clothes = Table(
    "favorite_clothes",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("clothes_id", ForeignKey("clothes.id", ondelete="CASCADE"), primary_key=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
)

favorite_patterns = Table(
    "favorite_patterns",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("pattern_id", ForeignKey("patterns.id", ondelete="CASCADE"), primary_key=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
)