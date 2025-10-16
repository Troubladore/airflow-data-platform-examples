"""Pagila Silver layer models (silver_pagila schema).

Silver layer applies strict business types and validation rules to Bronze data.
Failed transformations are quarantined in sl_transformation_errors table
following industry standard patterns.
"""

from .sl_customer import SlCustomer
from .sl_transformation_errors import SlTransformationError

__all__ = [
    "SlCustomer",
    "SlTransformationError",
]