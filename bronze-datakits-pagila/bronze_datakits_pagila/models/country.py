"""
Country Bronze Model using framework BronzeMetadata
"""

import sys
from datetime import datetime

sys.path.insert(0, '/home/emaynard/repos/airflow-data-platform/sqlmodel-framework/src')

from sqlmodel import SQLModel, Field
from sqlmodel_framework.base.models import BronzeMetadata


class CountryBronze(BronzeMetadata, SQLModel, table=True):
    """Bronze layer for Pagila country table"""

    __tablename__ = "bronze_country"
    __table_args__ = {"schema": "bronze"}

    country_id: int = Field(primary_key=True)
    country: str = Field(max_length=50)
    last_update: datetime