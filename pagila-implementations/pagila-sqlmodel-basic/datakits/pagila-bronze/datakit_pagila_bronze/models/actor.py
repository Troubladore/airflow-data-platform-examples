from datetime import datetime

# Removed mixin import to avoid table discovery conflicts
from sqlalchemy import TIMESTAMP, Column, text
from sqlmodel import Field, SQLModel


class BronzeActor(SQLModel, table=True):
    """Bronze layer actor table (br__pagila__public.actor)."""

    __tablename__ = "actor"
    __table_args__ = {"schema": "br__pagila__public"}

    # Source fields
    actor_id: int = Field(primary_key=True)
    first_name: str = Field(nullable=False)
    last_name: str = Field(nullable=False)
    source_last_update: datetime = Field(
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False)
    )

    # Bronze audit fields
    br_load_time: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("now()"),
        )
    )
    br_source_table: str = Field(default="public.actor", nullable=False)
    br_batch_id: str = Field(nullable=False)
    br_is_current: bool = Field(default=True, nullable=False)
    br_record_hash: str = Field(nullable=False)
