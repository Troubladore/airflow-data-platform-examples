from datetime import datetime

from sqlalchemy import TIMESTAMP, Column, text
from sqlmodel import Field, SQLModel


class Actor(SQLModel, table=True):
    """Pagila actor table (public.actor)."""

    __tablename__ = "actor"
    __table_args__ = {"schema": "public"}

    actor_id: int = Field(primary_key=True)
    first_name: str = Field(nullable=False)
    last_name: str = Field(nullable=False)
    last_update: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            default=text("now()"),
            server_default=text("now()"),
        )
    )
