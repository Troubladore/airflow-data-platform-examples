from datetime import datetime

from sqlalchemy import TIMESTAMP, Column, text
from sqlmodel import Field, SQLModel


class Country(SQLModel, table=True):
    """Pagila country table (public.country)."""

    __tablename__ = "country"
    __table_args__ = {"schema": "public"}

    country_id: int = Field(primary_key=True)
    country: str = Field(nullable=False, max_length=50)
    last_update: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("now()"),
        )
    )