"""Pagila Bronze layer models (staging_pagila schema).

These models represent the bronze warehouse layer with strict contract enforcement
and dead letter queue support for failed ingestion records.
"""

from .br_customer import BrCustomer
from .br_film import BrFilm
from .br_ingestion_errors import BrIngestionError

__all__ = [
    "BrCustomer",
    "BrFilm",
    "BrIngestionError",
]