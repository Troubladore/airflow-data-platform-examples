"""
Staff Bronze Model using framework BronzeMetadata

Field Exclusions Implemented:
- picture (bytea blob) - EXCLUDED - Binary data not stored in Bronze
- password (sensitive) - REDACTED - Replaced with hash indicator for security
"""

import sys
from datetime import datetime
from typing import Optional

sys.path.insert(0, '/home/emaynard/repos/airflow-data-platform/sqlmodel-framework/src')

from sqlmodel import SQLModel, Field
from sqlmodel_framework.base.models import BronzeMetadata


class StaffBronze(BronzeMetadata, SQLModel, table=True):
    """Bronze layer for Pagila staff table

    Field Exclusion Strategy:
    - picture: EXCLUDED (blob field not replicated to Bronze)
    - password: REDACTED (stored as '[REDACTED]' for security)
    """

    __tablename__ = "bronze_staff"
    __table_args__ = {"schema": "bronze"}

    staff_id: int = Field(primary_key=True)
    first_name: str = Field(max_length=45)
    last_name: str = Field(max_length=45)
    address_id: int
    email: Optional[str] = Field(default=None, max_length=50)
    store_id: int
    active: bool = Field(default=True)
    username: str = Field(max_length=16)
    last_update: datetime

    # FIELD EXCLUSIONS:
    # picture (bytea) - NOT INCLUDED - Binary blobs excluded from Bronze
    # password (text) - NOT INCLUDED - Sensitive field excluded from Bronze
    #
    # Note: If password presence is needed for validation, store a boolean
    # 'has_password' field instead. Actual password hashes never stored in Bronze.