"""
Language Bronze Model using framework BronzeMetadata
"""

import sys
from datetime import datetime

sys.path.insert(0, '/home/emaynard/repos/airflow-data-platform/sqlmodel-framework/src')

from sqlmodel import SQLModel, Field
from sqlmodel_framework.base.models import BronzeMetadata


class LanguageBronze(BronzeMetadata, SQLModel, table=True):
    """Bronze layer for Pagila language table"""

    __tablename__ = "bronze_language"
    __table_args__ = {"schema": "bronze"}

    language_id: int = Field(primary_key=True)
    name: str = Field(max_length=20)
    last_update: datetime