from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import TEXT, TIMESTAMP, Column, text
from sqlmodel import Field, SQLModel


class SlTransformationError(SQLModel, table=True):
    """Silver layer transformation error quarantine table.

    Industry standard pattern: quarantine failed Bronze→Silver transformations
    instead of failing the entire pipeline. Allows clean data to proceed while
    preserving failed records for analysis and remediation.
    """

    __tablename__ = "sl_transformation_errors"
    __table_args__ = {"schema": "silver_pagila"}

    # Error record identity
    error_id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Source record tracking
    br_source_key: UUID = Field(nullable=False)  # Reference to Bronze record
    source_table: str = Field(nullable=False, max_length=100)
    target_table: str = Field(nullable=False, max_length=100)
    batch_id: str = Field(nullable=False, max_length=100)

    # Bronze record data (preserved for analysis)
    bronze_record_json: str = Field(sa_column=Column(TEXT), nullable=False)

    # Error classification
    error_category: str = Field(nullable=False, max_length=50)  # DATA_TYPE, BUSINESS_RULE, MISSING_FIELD
    error_message: str = Field(sa_column=Column(TEXT), nullable=False)
    failed_field: Optional[str] = Field(default=None, max_length=100)
    expected_value: Optional[str] = Field(default=None, max_length=500)
    actual_value: Optional[str] = Field(default=None, max_length=500)

    # Business context
    transformation_rule: Optional[str] = Field(default=None, max_length=200)
    severity: str = Field(nullable=False, default="MEDIUM", max_length=20)  # LOW, MEDIUM, HIGH, CRITICAL

    # Remediation workflow
    remediation_status: str = Field(nullable=False, default="PENDING", max_length=50)  # PENDING, IN_PROGRESS, RESOLVED, IGNORED
    assigned_to: Optional[str] = Field(default=None, max_length=100)
    remediation_notes: Optional[str] = Field(default=None, sa_column=Column(TEXT))
    resolved_at: Optional[datetime] = Field(default=None)
    resolution_method: Optional[str] = Field(default=None, max_length=100)  # MANUAL_FIX, RULE_UPDATE, DATA_SOURCE_FIX

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

    # Alerting and monitoring
    alert_sent: bool = Field(default=False)
    alert_sent_at: Optional[datetime] = Field(default=None)
    impact_assessment: Optional[str] = Field(default=None, sa_column=Column(TEXT))