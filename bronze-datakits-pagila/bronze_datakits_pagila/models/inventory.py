"""
Inventory Bronze Model using framework BronzeMetadata
"""

import sys
from datetime import datetime

sys.path.insert(0, '/home/emaynard/repos/airflow-data-platform/sqlmodel-framework/src')

from sqlmodel import SQLModel, Field
from sqlmodel_framework.base.models import BronzeMetadata


class InventoryBronze(BronzeMetadata, SQLModel, table=True):
    """Bronze layer for Pagila inventory table"""

    __tablename__ = "bronze_inventory"
    __table_args__ = {"schema": "bronze"}

    inventory_id: int = Field(primary_key=True)
    film_id: int
    store_id: int
    last_update: datetime