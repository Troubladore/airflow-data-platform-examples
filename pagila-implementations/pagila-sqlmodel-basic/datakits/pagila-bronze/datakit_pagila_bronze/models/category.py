from datetime import datetime

# Removed mixin import to avoid table discovery conflicts
from sqlalchemy import TIMESTAMP, Column, text
from sqlmodel import Field, SQLModel


class BronzeCategory(SQLModel, table=True):
    """Bronze layer category table (br__pagila__public.category)."""

    __tablename__ = "category"
    __table_args__ = {"schema": "br__pagila__public"}

    # Source fields (no constraints in bronze)
    category_id: int = Field(primary_key=True)
    name: str = Field(nullable=False)
    source_last_update: datetime = Field(
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False)
    )

    # Bronze audit fields:
    br_load_time: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            default=text("now()"),
            server_default=text("now()"),
        )
    )
    br_source_table: str = Field(default="public.category", nullable=False)
    br_batch_id: str = Field(nullable=False)
    br_is_current: bool = Field(default=True, nullable=False)
    br_record_hash: str = Field(nullable=False)
