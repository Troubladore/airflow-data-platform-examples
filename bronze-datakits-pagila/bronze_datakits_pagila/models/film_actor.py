"""
FilmActor Bronze Model using framework BronzeMetadata
"""

import sys
from datetime import datetime

sys.path.insert(0, '/home/emaynard/repos/airflow-data-platform/sqlmodel-framework/src')

from sqlmodel import SQLModel, Field
from sqlmodel_framework.base.models import BronzeMetadata


class FilmActorBronze(BronzeMetadata, SQLModel, table=True):
    """Bronze layer for Pagila film_actor junction table"""

    __tablename__ = "bronze_film_actor"
    __table_args__ = {"schema": "bronze"}

    actor_id: int = Field(primary_key=True)
    film_id: int = Field(primary_key=True)
    last_update: datetime