from datetime import datetime, date
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import TIMESTAMP, Column, text
from sqlmodel import Field, SQLModel


class BrCustomer(SQLModel, table=True):
    """Bronze layer customer table (staging_pagila.br_customer).

    Enforces strict data contracts from source pagila.customer with audit fields.
    FAILS FAST on type mismatches to detect source system changes immediately.
    """

    __tablename__ = "br_customer"
    __table_args__ = {"schema": "staging_pagila"}

    # Bronze surrogate key
    br_customer_key: UUID = Field(default_factory=uuid4, primary_key=True)

    # Source data fields (STRICT CONTRACT ENFORCEMENT - fail fast on schema changes)
    customer_id: int = Field(nullable=False)  # Contract: must be integer, required
    store_id: int = Field(nullable=False)  # Contract: must be integer, required
    first_name: str = Field(nullable=False)  # Contract: must be string, required
    last_name: str = Field(nullable=False)  # Contract: must be string, required
    email: str | None = Field(default=None, nullable=True)  # Contract: string or null (optional)
    address_id: int = Field(nullable=False)  # Contract: must be integer, required
    activebool: bool = Field(nullable=False, default=True)  # Contract: must be boolean, required
    create_date: date = Field(nullable=False)  # Contract: must be date, required
    last_update: datetime | None = Field(default=None, nullable=True)  # Contract: datetime or null
    active: int | None = Field(default=None, nullable=True)  # Contract: integer or null

    # Bronze audit fields
    br_load_time: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("now()")
        )
    )
    br_source_file: Optional[str] = Field(default=None, nullable=True, max_length=500)
    br_record_hash: Optional[str] = Field(default=None, nullable=True, max_length=64)
    br_is_current: bool = Field(default=True, nullable=False)
    br_batch_id: Optional[str] = Field(default=None, nullable=True, max_length=100)