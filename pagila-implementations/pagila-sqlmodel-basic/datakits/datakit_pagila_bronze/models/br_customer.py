from datetime import datetime, date
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import TIMESTAMP, Column, text
from sqlmodel import Field, SQLModel


class BrCustomer(SQLModel, table=True):
    """Bronze layer customer table (staging_pagila.br_customer).

    Industry standard Bronze pattern: lenient typing to prevent data loss.
    All source fields stored as Optional[str] to capture any data format.
    Type validation and business rules applied in Bronze→Silver transformation.
    """

    __tablename__ = "br_customer"
    __table_args__ = {"schema": "staging_pagila"}

    # Bronze surrogate key
    br_customer_key: UUID = Field(default_factory=uuid4, primary_key=True)

    # Source data fields (LENIENT TYPING - industry standard Bronze pattern)
    customer_id: Optional[str] = Field(default=None, nullable=True)  # Store as text to prevent data loss
    store_id: Optional[str] = Field(default=None, nullable=True)
    first_name: Optional[str] = Field(default=None, nullable=True)
    last_name: Optional[str] = Field(default=None, nullable=True)
    email: Optional[str] = Field(default=None, nullable=True)
    address_id: Optional[str] = Field(default=None, nullable=True)
    activebool: Optional[str] = Field(default=None, nullable=True)  # TEXT to handle varied boolean representations
    create_date: Optional[str] = Field(default=None, nullable=True)  # TEXT to handle varied date formats
    last_update: Optional[str] = Field(default=None, nullable=True)
    active: Optional[str] = Field(default=None, nullable=True)

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