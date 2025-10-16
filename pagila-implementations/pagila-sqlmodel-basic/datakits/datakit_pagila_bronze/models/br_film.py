from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import TIMESTAMP, Column, text
from sqlmodel import Field, SQLModel


class BrFilm(SQLModel, table=True):
    """Bronze layer film table (staging_pagila.br_film).

    Ingests data from source pagila.film with audit fields and lenient typing
    to handle data quality issues during initial ingestion.
    """

    __tablename__ = "br_film"
    __table_args__ = {"schema": "staging_pagila"}

    # Bronze surrogate key
    br_film_key: UUID = Field(default_factory=uuid4, primary_key=True)

    # Source data fields (lenient types for data quality handling)
    film_id: Optional[str] = Field(default=None, nullable=True)
    title: Optional[str] = Field(default=None, nullable=True)
    description: Optional[str] = Field(default=None, nullable=True)
    release_year: Optional[str] = Field(default=None, nullable=True)
    language_id: Optional[str] = Field(default=None, nullable=True)
    rental_duration: Optional[str] = Field(default=None, nullable=True)
    rental_rate: Optional[str] = Field(default=None, nullable=True)
    length: Optional[str] = Field(default=None, nullable=True)
    replacement_cost: Optional[str] = Field(default=None, nullable=True)
    rating: Optional[str] = Field(default=None, nullable=True)
    special_features: Optional[str] = Field(default=None, nullable=True)
    last_update: Optional[str] = Field(default=None, nullable=True)

    # Bronze audit fields
    br_load_time: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("now()")
        )
    )
    br_source_file: Optional[str] = Field(default=None, nullable=True, max_length=500)
    br_record_hash: Optional[str] = Field(default=None, nullable=True, max_length=64)
    br_is_current: bool = Field(default=True, nullable=False)
    br_batch_id: Optional[str] = Field(default=None, nullable=True, max_length=100)