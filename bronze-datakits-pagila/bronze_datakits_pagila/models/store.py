"""
Store Bronze Model using framework BronzeMetadata
"""

import sys
from datetime import datetime

sys.path.insert(0, '/home/emaynard/repos/airflow-data-platform/sqlmodel-framework/src')

from sqlmodel import SQLModel, Field
from sqlmodel_framework.base.models import BronzeMetadata


class StoreBronze(BronzeMetadata, SQLModel, table=True):
    """Bronze layer for Pagila store table"""

    __tablename__ = "bronze_store"
    __table_args__ = {"schema": "bronze"}

    store_id: int = Field(primary_key=True)
    manager_staff_id: int
    address_id: int
    last_update: datetime