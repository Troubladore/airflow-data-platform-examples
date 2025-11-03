"""
City Bronze Model using framework BronzeMetadata
"""

import sys
from datetime import datetime

sys.path.insert(0, '/home/emaynard/repos/airflow-data-platform/sqlmodel-framework/src')

from sqlmodel import SQLModel, Field
from sqlmodel_framework.base.models import BronzeMetadata


class CityBronze(BronzeMetadata, SQLModel, table=True):
    """Bronze layer for Pagila city table"""

    __tablename__ = "bronze_city"
    __table_args__ = {"schema": "bronze"}

    city_id: int = Field(primary_key=True)
    city: str = Field(max_length=50)
    country_id: int
    last_update: datetime