from datetime import datetime

from sqlalchemy import TIMESTAMP, Column, ForeignKey, text
from sqlmodel import Field, SQLModel


class Store(SQLModel, table=True):
    """Pagila store table (public.store)."""

    __tablename__ = "store"
    __table_args__ = {"schema": "public"}

    store_id: int = Field(primary_key=True)
    manager_staff_id: int = Field(
        sa_column=Column(ForeignKey("public.staff.staff_id"), nullable=False)
    )
    address_id: int = Field(
        sa_column=Column(ForeignKey("public.address.address_id"), nullable=False)
    )
    last_update: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("now()"),
        )
    )