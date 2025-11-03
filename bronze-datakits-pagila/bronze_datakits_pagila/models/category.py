"""
Category Bronze Model using framework BronzeMetadata

This model represents the Bronze layer for the Pagila category table.
"""

import sys
from datetime import datetime

# Add framework to path for imports
sys.path.insert(0, '/home/emaynard/repos/airflow-data-platform/sqlmodel-framework/src')

from sqlmodel import SQLModel, Field
from sqlmodel_framework.base.models import BronzeMetadata


class CategoryBronze(BronzeMetadata, SQLModel, table=True):
    """Bronze layer for Pagila category table"""

    __tablename__ = "bronze_category"
    __table_args__ = {"schema": "bronze"}

    # Primary key from source
    category_id: int = Field(primary_key=True)

    # Required source fields
    name: str = Field(max_length=25)
    last_update: datetime

    # Bronze metadata fields are inherited from BronzeMetadata