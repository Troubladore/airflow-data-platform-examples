from datetime import datetime

from sqlalchemy import TIMESTAMP, Column, ForeignKey, text
from sqlmodel import Field, SQLModel


class Staff(SQLModel, table=True):
    """Pagila staff table (public.staff)."""

    __tablename__ = "staff"
    __table_args__ = {"schema": "public"}

    staff_id: int = Field(primary_key=True)
    first_name: str = Field(nullable=False, max_length=45)
    last_name: str = Field(nullable=False, max_length=45)
    address_id: int = Field(
        sa_column=Column(ForeignKey("public.address.address_id"), nullable=False)
    )
    picture: bytes | None = Field(default=None)
    email: str | None = Field(default=None, max_length=50)
    store_id: int = Field(
        sa_column=Column(ForeignKey("public.store.store_id"), nullable=False)
    )
    active: bool = Field(default=True)
    username: str = Field(nullable=False, max_length=16)
    password: str | None = Field(default=None, max_length=40)
    last_update: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("now()"),
        )
    )