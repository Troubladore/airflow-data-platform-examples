"""Bronze layer models for Pagila warehouse ingestion (br__pagila__public schema).

These models define the bronze layer warehouse tables with:
- Schema: br__pagila__public
- No referential constraints for fast parallel loading
- Audit columns: br_load_time, br_batch_id, br_record_hash, br_is_current
- Source tracking: br_source_table
"""

from .actor import BronzeActor
from .category import BronzeCategory
from .customer import BronzeCustomer
from .film import BronzeFilm
from .inventory import BronzeInventory
from .rental import BronzeRental

__all__ = [
    "BronzeCategory",
    "BronzeFilm",
    "BronzeActor",
    "BronzeCustomer",
    "BronzeRental",
    "BronzeInventory",
]
