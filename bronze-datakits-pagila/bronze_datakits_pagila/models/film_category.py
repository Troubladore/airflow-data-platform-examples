"""
FilmCategory Bronze Model using framework BronzeMetadata
"""

import sys
from datetime import datetime

sys.path.insert(0, '/home/emaynard/repos/airflow-data-platform/sqlmodel-framework/src')

from sqlmodel import SQLModel, Field
from sqlmodel_framework.base.models import BronzeMetadata


class FilmCategoryBronze(BronzeMetadata, SQLModel, table=True):
    """Bronze layer for Pagila film_category junction table"""

    __tablename__ = "bronze_film_category"
    __table_args__ = {"schema": "bronze"}

    film_id: int = Field(primary_key=True)
    category_id: int = Field(primary_key=True)
    last_update: datetime