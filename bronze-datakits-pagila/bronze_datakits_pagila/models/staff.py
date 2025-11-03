"""
Staff Bronze Model using framework BronzeMetadata
"""

import sys
from datetime import datetime
from typing import Optional

sys.path.insert(0, '/home/emaynard/repos/airflow-data-platform/sqlmodel-framework/src')

from sqlmodel import SQLModel, Field
from sqlmodel_framework.base.models import BronzeMetadata


class StaffBronze(BronzeMetadata, SQLModel, table=True):
    """Bronze layer for Pagila staff table"""

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
    password: Optional[str] = Field(default=None, max_length=40)
    last_update: datetime
    picture: Optional[bytes] = Field(default=None)