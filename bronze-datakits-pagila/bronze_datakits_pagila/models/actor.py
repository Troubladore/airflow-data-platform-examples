"""
Actor Bronze Model using framework BronzeMetadata

This model represents the Bronze layer for the Pagila actor table.
"""

import sys
from datetime import datetime
from typing import Optional

# Add framework to path for imports
sys.path.insert(0, '/home/emaynard/repos/airflow-data-platform/sqlmodel-framework/src')

from sqlmodel import SQLModel, Field
from sqlmodel_framework.base.models import BronzeMetadata


class ActorBronze(BronzeMetadata, SQLModel, table=True):
    """Bronze layer for Pagila actor table"""

    __tablename__ = "bronze_actor"
    __table_args__ = {"schema": "bronze"}

    # Primary key from source
    actor_id: int = Field(primary_key=True)

    # Required source fields
    first_name: str = Field(max_length=45)
    last_name: str = Field(max_length=45)
    last_update: datetime

    # Bronze metadata fields are inherited from BronzeMetadata