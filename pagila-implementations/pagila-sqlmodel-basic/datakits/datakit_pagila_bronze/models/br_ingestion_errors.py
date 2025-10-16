from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import TEXT, TIMESTAMP, Column, text
from sqlmodel import Field, SQLModel


class BrIngestionError(SQLModel, table=True):
    """Dead letter queue for Bronze layer ingestion failures.

    Captures records that fail strict contract validation during Bronze ingestion,
    allowing for later analysis and remediation while maintaining data lineage.

    Two failure modes supported:
    1. Schema validation failures (type mismatches, missing required fields)
    2. Business rule violations (invalid foreign keys, constraint violations)
    """

    __tablename__ = "br_ingestion_errors"
    __table_args__ = {"schema": "staging_pagila"}

    # Error record identity
    error_id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Source context
    source_table: str = Field(nullable=False, max_length=100)
    source_system: str = Field(nullable=False, max_length=100, default="pagila")
    batch_id: str = Field(nullable=False, max_length=100)

    # Failed record data (preserved as JSON/text)
    raw_record: str = Field(sa_column=Column(TEXT), nullable=False)  # Original record as JSON

    # Error classification
    error_type: str = Field(nullable=False, max_length=50)  # 'SCHEMA_VALIDATION', 'CONSTRAINT_VIOLATION'
    error_message: str = Field(sa_column=Column(TEXT), nullable=False)
    failed_field: Optional[str] = Field(default=None, max_length=100)
    expected_type: Optional[str] = Field(default=None, max_length=100)
    actual_value: Optional[str] = Field(default=None, max_length=500)

    # Remediation tracking
    remediation_status: str = Field(nullable=False, default="PENDING", max_length=50)  # PENDING, FIXED, IGNORED
    remediation_notes: Optional[str] = Field(default=None, sa_column=Column(TEXT))
    remediated_at: Optional[datetime] = Field(default=None)
    remediated_by: Optional[str] = Field(default=None, max_length=100)

    # Audit fields
    created_at: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("now()")
        )
    )
    retry_count: int = Field(default=0, nullable=False)
    last_retry_at: Optional[datetime] = Field(default=None)