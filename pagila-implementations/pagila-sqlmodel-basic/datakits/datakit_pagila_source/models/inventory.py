from datetime import datetime

from sqlalchemy import TIMESTAMP, Column, ForeignKey, text
from sqlmodel import Field, SQLModel


class Inventory(SQLModel, table=True):
    """Pagila inventory table (public.inventory)."""

    __tablename__ = "inventory"
    __table_args__ = {"schema": "public"}

    inventory_id: int = Field(primary_key=True)
    film_id: int = Field(
        sa_column=Column(ForeignKey("public.film.film_id"), nullable=False)
    )
    store_id: int = Field(
        sa_column=Column(ForeignKey("public.store.store_id"), nullable=False)
    )
    last_update: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("now()"),
        )
    )
