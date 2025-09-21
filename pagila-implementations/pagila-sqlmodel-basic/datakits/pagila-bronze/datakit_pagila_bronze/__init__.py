"""Pagila Bronze Layer Datakit - Warehouse ingestion tables.

This datakit provides bronze layer tables using the schema pattern:
br__pagila__public.*

Bronze tables include:
- No referential constraints (fast parallel loading)
- Audit/tracking columns (load_time, batch_id, record_hash, etc.)
- Type-safe transforms from pagila source to warehouse bronze layer
"""

__version__ = "0.1.0"
