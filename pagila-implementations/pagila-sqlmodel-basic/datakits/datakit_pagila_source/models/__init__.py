"""Pagila source database models (public schema).

These models represent the original Pagila database schema structure
for type-safe reading of source data.
"""

from .actor import Actor
from .category import Category
from .customer import Customer
from .film import Film, MPAARating
from .inventory import Inventory
from .rental import Rental

__all__ = [
    "Category",
    "Film",
    "MPAARating",
    "Actor",
    "Customer",
    "Rental",
    "Inventory",
]
