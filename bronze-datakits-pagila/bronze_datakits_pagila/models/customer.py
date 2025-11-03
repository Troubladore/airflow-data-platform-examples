"""
Customer Bronze Model using framework BronzeMetadata

This model represents the Bronze layer for the Pagila customer table.
"""

import sys
from datetime import datetime, date
from typing import Optional

# Add framework to path for imports
sys.path.insert(0, '/home/emaynard/repos/airflow-data-platform/sqlmodel-framework/src')

from sqlmodel import SQLModel, Field
from sqlmodel_framework.base.models import BronzeMetadata


class CustomerBronze(BronzeMetadata, SQLModel, table=True):
    """Bronze layer for Pagila customer table"""

    __tablename__ = "bronze_customer"
    __table_args__ = {"schema": "bronze"}

    # Primary key from source
    customer_id: int = Field(primary_key=True)

    # Required source fields
    store_id: int
    first_name: str = Field(max_length=45)
    last_name: str = Field(max_length=45)
    address_id: int
    active: bool = Field(default=True)
    create_date: date
    last_update: datetime

    # Optional source fields
    email: Optional[str] = Field(default=None, max_length=50)

    # Bronze metadata fields are inherited from BronzeMetadata