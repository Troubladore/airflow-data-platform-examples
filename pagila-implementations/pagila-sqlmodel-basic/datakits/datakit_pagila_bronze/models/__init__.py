"""Pagila Bronze layer models (staging_pagila schema).

These models represent the bronze warehouse layer with audit fields
and lenient typing to handle data quality issues during ingestion
from the source Pagila database.
"""

from .br_customer import BrCustomer
from .br_film import BrFilm

__all__ = [
    "BrCustomer",
    "BrFilm",
]