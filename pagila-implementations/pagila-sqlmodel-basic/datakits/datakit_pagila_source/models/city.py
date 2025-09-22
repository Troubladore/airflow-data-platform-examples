from datetime import datetime

from sqlalchemy import TIMESTAMP, Column, ForeignKey, text
from sqlmodel import Field, SQLModel


class City(SQLModel, table=True):
    """Pagila city table (public.city)."""

    __tablename__ = "city"
    __table_args__ = {"schema": "public"}

    city_id: int = Field(primary_key=True)
    city: str = Field(nullable=False, max_length=50)
    country_id: int = Field(
        sa_column=Column(ForeignKey("public.country.country_id"), nullable=False)
    )
    last_update: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("now()"),
        )
    )