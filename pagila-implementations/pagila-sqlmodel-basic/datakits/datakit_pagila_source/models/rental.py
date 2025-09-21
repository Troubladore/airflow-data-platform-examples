from datetime import datetime

from sqlalchemy import TIMESTAMP, Column, ForeignKey, text
from sqlmodel import Field, SQLModel


class Rental(SQLModel, table=True):
    """Pagila rental transaction table (public.rental)."""

    __tablename__ = "rental"
    __table_args__ = {"schema": "public"}

    rental_id: int = Field(primary_key=True)
    rental_date: datetime = Field(
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False)
    )
    inventory_id: int = Field(
        sa_column=Column(ForeignKey("public.inventory.inventory_id"), nullable=False)
    )
    customer_id: int = Field(
        sa_column=Column(ForeignKey("public.customer.customer_id"), nullable=False)
    )
    return_date: datetime | None = Field(
        sa_column=Column(TIMESTAMP(timezone=True), nullable=True), default=None
    )
    staff_id: int = Field(
        sa_column=Column(ForeignKey("public.staff.staff_id"), nullable=False)
    )
    last_update: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            default=text("now()"),
            server_default=text("now()"),
        )
    )
