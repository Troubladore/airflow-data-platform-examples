"""Pagila source database models (public schema).

These models represent the original Pagila database schema structure
for type-safe reading of source data.
"""

from .actor import Actor
from .address import Address
from .category import Category
from .city import City
from .country import Country
from .customer import Customer
from .film import Film, MPAARating
from .inventory import Inventory
from .language import Language
from .rental import Rental
from .staff import Staff
from .store import Store

__all__ = [
    "Address",
    "Actor",
    "Category",
    "City",
    "Country",
    "Customer",
    "Film",
    "Inventory",
    "Language",
    "MPAARating",
    "Rental",
    "Staff",
    "Store",
]
