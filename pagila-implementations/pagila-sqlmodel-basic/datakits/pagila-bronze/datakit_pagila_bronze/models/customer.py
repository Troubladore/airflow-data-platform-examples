from datetime import date, datetime

# Removed mixin import to avoid table discovery conflicts
from sqlalchemy import DATE, TIMESTAMP, Column, text
from sqlmodel import Field, SQLModel


class BronzeCustomer(SQLModel, table=True):
    """Bronze layer customer table (br__pagila__public.customer)."""

    __tablename__ = "customer"
    __table_args__ = {"schema": "br__pagila__public"}

    # Source fields (no FK constraints)
    customer_id: int = Field(primary_key=True)
    store_id: int = Field(nullable=False)  # No FK
    first_name: str = Field(nullable=False)
    last_name: str = Field(nullable=False)
    email: str | None = Field(default=None, nullable=True)
    address_id: int = Field(nullable=False)  # No FK
    activebool: bool = Field(nullable=False, default=True)
    create_date: date = Field(sa_column=Column(DATE, nullable=False))
    source_last_update: datetime | None = Field(
        sa_column=Column(TIMESTAMP(timezone=True), nullable=True)
    )
    active: int | None = Field(default=None, nullable=True)

    # Bronze audit fields (TransactionalTableMixin provides created_at, updated_at)
    br_load_time: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("now()"),
        )
    )
    br_source_table: str = Field(default="public.customer", nullable=False)
    br_batch_id: str = Field(nullable=False)
    br_is_current: bool = Field(default=True, nullable=False)
    br_record_hash: str = Field(nullable=False)
