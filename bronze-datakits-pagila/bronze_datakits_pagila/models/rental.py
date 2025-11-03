"""
Rental Bronze Model using framework BronzeMetadata
"""

import sys
from datetime import datetime
from typing import Optional

sys.path.insert(0, '/home/emaynard/repos/airflow-data-platform/sqlmodel-framework/src')

from sqlmodel import SQLModel, Field
from sqlmodel_framework.base.models import BronzeMetadata


class RentalBronze(BronzeMetadata, SQLModel, table=True):
    """Bronze layer for Pagila rental table"""

    __tablename__ = "bronze_rental"
    __table_args__ = {"schema": "bronze"}

    rental_id: int = Field(primary_key=True)
    rental_date: datetime
    inventory_id: int
    customer_id: int
    return_date: Optional[datetime] = Field(default=None)
    staff_id: int
    last_update: datetime