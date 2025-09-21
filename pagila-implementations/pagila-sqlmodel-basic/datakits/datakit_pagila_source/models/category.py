from datetime import datetime

from sqlalchemy import TIMESTAMP, Column, text
from sqlmodel import Field, SQLModel


class Category(SQLModel, table=True):
    """Pagila category reference table (public.category)."""

    __tablename__ = "category"
    __table_args__ = {"schema": "public"}

    category_id: int = Field(primary_key=True)
    name: str = Field(nullable=False)
    last_update: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("now()"),
        )
    )
