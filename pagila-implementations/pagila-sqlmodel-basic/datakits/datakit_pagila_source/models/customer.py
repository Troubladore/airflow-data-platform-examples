from datetime import date, datetime

from sqlalchemy import DATE, TIMESTAMP, Column, ForeignKey, text
from sqlmodel import Field, SQLModel


class Customer(SQLModel, table=True):
    """Pagila customer table (public.customer)."""

    __tablename__ = "customer"
    __table_args__ = {"schema": "public"}

    customer_id: int = Field(primary_key=True)
    store_id: int = Field(
        sa_column=Column(ForeignKey("public.store.store_id"), nullable=False)
    )
    first_name: str = Field(nullable=False)
    last_name: str = Field(nullable=False)
    email: str | None = Field(default=None, nullable=True)
    address_id: int = Field(
        sa_column=Column(ForeignKey("public.address.address_id"), nullable=False)
    )
    activebool: bool = Field(nullable=False, default=True, server_default=text("true"))
    create_date: date = Field(
        sa_column=Column(
            DATE,
            nullable=False,
            default=text("('now'::text)::date"),
            server_default=text("('now'::text)::date"),
        )
    )
    last_update: datetime | None = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=True,
            default=text("now()"),
            server_default=text("now()"),
        )
    )
    active: int | None = Field(default=None, nullable=True)
