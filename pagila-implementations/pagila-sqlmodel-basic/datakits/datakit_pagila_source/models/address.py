from datetime import datetime

from sqlalchemy import TIMESTAMP, Column, ForeignKey, text
from sqlmodel import Field, SQLModel


class Address(SQLModel, table=True):
    """Pagila address table (public.address)."""

    __tablename__ = "address"
    __table_args__ = {"schema": "public"}

    address_id: int = Field(primary_key=True)
    address: str = Field(nullable=False, max_length=50)
    address2: str | None = Field(default=None, max_length=50)
    district: str = Field(nullable=False, max_length=20)
    city_id: int = Field(
        sa_column=Column(ForeignKey("public.city.city_id"), nullable=False)
    )
    postal_code: str | None = Field(default=None, max_length=10)
    phone: str = Field(nullable=False, max_length=20)
    last_update: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("now()"),
        )
    )