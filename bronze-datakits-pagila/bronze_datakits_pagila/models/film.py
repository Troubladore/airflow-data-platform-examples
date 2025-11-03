"""
Film Bronze Model using framework BronzeMetadata

This model represents the Bronze layer for the Pagila film table,
using the sqlmodel-framework's BronzeMetadata mixin for standardized
metadata tracking.
"""

import sys
from datetime import datetime
from typing import Optional

# Add framework to path for imports
sys.path.insert(0, '/home/emaynard/repos/airflow-data-platform/sqlmodel-framework/src')

from sqlmodel import SQLModel, Field
from sqlmodel_framework.base.models import BronzeMetadata


class FilmBronze(BronzeMetadata, SQLModel, table=True):
    """Bronze layer for Pagila film table"""

    __tablename__ = "bronze_film"
    __table_args__ = {"schema": "bronze"}

    # Primary key from source
    film_id: int = Field(primary_key=True)

    # Required source fields
    title: str = Field(max_length=255)
    language_id: int
    last_update: datetime

    # Optional source fields with defaults
    description: Optional[str] = Field(default=None)
    release_year: Optional[int] = Field(default=None)
    original_language_id: Optional[int] = Field(default=None)
    rental_duration: int = Field(default=3)
    rental_rate: float = Field(default=4.99)
    length: Optional[int] = Field(default=None)  # Minutes
    replacement_cost: float = Field(default=19.99)
    rating: str = Field(default="G", max_length=10)

    # PostgreSQL-specific fields stored as text in Bronze
    special_features: Optional[str] = Field(
        default=None,
        description="Special features list (was array in source)"
    )
    fulltext: Optional[str] = Field(
        default=None,
        description="Full-text search data (was tsvector in source)"
    )

    # Bronze metadata fields are inherited from BronzeMetadata:
    # - bronze_load_timestamp: datetime
    # - bronze_source_system: str
    # - bronze_source_table: str
    # - bronze_source_host: str
    # - bronze_extraction_method: str