"""
Address Bronze Model using framework BronzeMetadata

This model represents the Bronze layer for the Pagila address table.
"""

import sys
from datetime import datetime
from typing import Optional

# Add framework to path for imports
sys.path.insert(0, '/home/emaynard/repos/airflow-data-platform/sqlmodel-framework/src')

from sqlmodel import SQLModel, Field
from sqlmodel_framework.base.models import BronzeMetadata


class AddressBronze(BronzeMetadata, SQLModel, table=True):
    """Bronze layer for Pagila address table"""

    __tablename__ = "bronze_address"
    __table_args__ = {"schema": "bronze"}

    # Primary key from source
    address_id: int = Field(primary_key=True)

    # Required source fields
    address: str = Field(max_length=50)
    district: str = Field(max_length=20)
    city_id: int
    postal_code: Optional[str] = Field(default=None, max_length=10)
    phone: str = Field(max_length=20)
    last_update: datetime

    # Optional fields
    address2: Optional[str] = Field(default=None, max_length=50)

    # Bronze metadata fields are inherited from BronzeMetadata