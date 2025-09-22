from datetime import datetime, date
from typing import Optional
from uuid import UUID

from sqlalchemy import DATE, TIMESTAMP, Column, text
from sqlmodel import Field, SQLModel


class SlCustomer(SQLModel, table=True):
    """Silver layer customer table (silver_pagila.sl_customer).

    Applies strict business types and validation rules to Bronze data.
    Failed transformations are quarantined in sl_transformation_errors.
    """

    __tablename__ = "sl_customer"
    __table_args__ = {"schema": "silver_pagila"}

    # Silver surrogate key (references bronze key for lineage)
    sl_customer_key: UUID = Field(primary_key=True)
    br_customer_key: UUID = Field(nullable=False)  # Lineage to Bronze

    # Business data fields (STRICT TYPING - validated from Bronze)
    customer_id: int = Field(nullable=False)
    store_id: int = Field(nullable=False)
    first_name: str = Field(nullable=False, max_length=100)
    last_name: str = Field(nullable=False, max_length=100)
    email: Optional[str] = Field(default=None, max_length=255)
    address_id: int = Field(nullable=False)
    is_active: bool = Field(nullable=False)  # Cleaned from Bronze activebool
    create_date: date = Field(sa_column=Column(DATE, nullable=False))
    last_update: Optional[datetime] = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=True)
    )
    active_flag: Optional[int] = Field(default=None)

    # Silver business logic fields
    full_name: str = Field(nullable=False, max_length=201)  # first_name + last_name
    email_domain: Optional[str] = Field(default=None, max_length=100)  # Extracted from email
    customer_tenure_days: Optional[int] = Field(default=None)  # Days since create_date
    is_email_valid: bool = Field(default=False)  # Email format validation result

    # Silver audit fields
    sl_load_time: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("now()")
        )
    )
    sl_batch_id: str = Field(nullable=False, max_length=100)
    sl_source_system: str = Field(nullable=False, default="pagila", max_length=50)
    sl_data_quality_score: Optional[float] = Field(default=None)  # 0.0-1.0 quality score