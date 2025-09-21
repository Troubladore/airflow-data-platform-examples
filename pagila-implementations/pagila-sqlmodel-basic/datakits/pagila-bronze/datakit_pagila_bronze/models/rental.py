from datetime import datetime

# Removed mixin import to avoid table discovery conflicts
from sqlalchemy import TIMESTAMP, Column, text
from sqlmodel import Field, SQLModel


class BronzeRental(SQLModel, table=True):
    """Bronze layer rental transaction table (br__pagila__public.rental)."""

    __tablename__ = "rental"
    __table_args__ = {"schema": "br__pagila__public"}

    # Source fields (no FK constraints)
    rental_id: int = Field(primary_key=True)
    rental_date: datetime = Field(
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False)
    )
    inventory_id: int = Field(nullable=False)  # No FK
    customer_id: int = Field(nullable=False)  # No FK
    return_date: datetime | None = Field(
        sa_column=Column(TIMESTAMP(timezone=True), nullable=True), default=None
    )
    staff_id: int = Field(nullable=False)  # No FK
    source_last_update: datetime = Field(
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False)
    )

    # Bronze audit fields
    br_load_time: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            default=text("now()"),
            server_default=text("now()"),
        )
    )
    br_source_table: str = Field(default="public.rental", nullable=False)
    br_batch_id: str = Field(nullable=False)
    br_is_current: bool = Field(default=True, nullable=False)
    br_record_hash: str = Field(nullable=False)
