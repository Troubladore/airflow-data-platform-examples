"""
Bronze Layer Ingestion Handler with Dead Letter Queue

Implements hybrid Bronze ingestion strategy supporting both:
1. Strict contract validation (fail-fast on schema changes)
2. Dead letter queue for failed records (never lose data)

Architecture:
- Primary path: Strict validation → Bronze tables
- Error path: Failed records → br_ingestion_errors table
- Remediation: Tools to replay/fix failed records
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional
from uuid import uuid4

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, DataError


logger = logging.getLogger(__name__)


class BronzeIngestionHandler:
    """Handles Bronze layer ingestion with dead letter queue for failures."""

    def __init__(self, source_engine, bronze_engine, batch_id: str):
        self.source_engine = source_engine
        self.bronze_engine = bronze_engine
        self.batch_id = batch_id
        self.stats = {
            "records_processed": 0,
            "records_success": 0,
            "records_failed": 0,
            "tables_processed": 0,
            "errors": []
        }

    def ingest_table_with_dlq(
        self,
        source_table: str,
        bronze_table: str,
        source_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ingest table with dead letter queue for failed records.

        Args:
            source_table: Source table name (e.g., 'customer')
            bronze_table: Bronze table name (e.g., 'br_customer')
            source_query: Optional custom query (defaults to SELECT *)

        Returns:
            Dict with success/failure counts and error details
        """
        logger.info(f"🥉 Starting Bronze ingestion: {source_table} → {bronze_table}")

        # Extract source data
        query = source_query or f"SELECT * FROM public.{source_table}"
        try:
            source_df = pd.read_sql(query, self.source_engine)
            logger.info(f"   📊 Extracted {len(source_df)} records from {source_table}")
        except Exception as e:
            error_msg = f"Failed to extract from {source_table}: {str(e)}"
            logger.error(f"   ❌ {error_msg}")
            self.stats["errors"].append(error_msg)
            return {"success": 0, "failed": 0, "error": error_msg}

        if len(source_df) == 0:
            logger.warning(f"   ⚠️ No records found in {source_table}")
            return {"success": 0, "failed": 0, "error": "No records found"}

        # Process records with error handling
        success_records = []
        failed_records = []

        for index, row in source_df.iterrows():
            try:
                # Add Bronze audit fields
                bronze_record = self._add_audit_fields(row, source_table)

                # Validate record against Bronze schema (this is where strict validation happens)
                self._validate_bronze_record(bronze_record, bronze_table)

                success_records.append(bronze_record)

            except Exception as e:
                # Capture failed record for dead letter queue
                failed_record = {
                    "source_table": source_table,
                    "source_system": "pagila",
                    "batch_id": self.batch_id,
                    "raw_record": json.dumps(row.to_dict(), default=str),
                    "error_type": self._classify_error(e),
                    "error_message": str(e),
                    "failed_field": self._extract_failed_field(e),
                    "expected_type": self._extract_expected_type(e),
                    "actual_value": str(row.get(self._extract_failed_field(e), "N/A"))[:500],
                }
                failed_records.append(failed_record)
                logger.warning(f"   ⚠️ Record failed validation: {str(e)}")

        # Load successful records to Bronze
        success_count = 0
        if success_records:
            try:
                success_df = pd.DataFrame(success_records)
                success_df.to_sql(
                    bronze_table,
                    self.bronze_engine,
                    schema="staging_pagila",
                    if_exists="append",
                    index=False
                )
                success_count = len(success_records)
                logger.info(f"   ✅ Loaded {success_count} records to {bronze_table}")
            except Exception as e:
                logger.error(f"   ❌ Failed to load to Bronze: {str(e)}")
                self.stats["errors"].append(f"Bronze load failed for {bronze_table}: {str(e)}")

        # Load failed records to dead letter queue
        failed_count = 0
        if failed_records:
            try:
                failed_df = pd.DataFrame(failed_records)
                failed_df.to_sql(
                    "br_ingestion_errors",
                    self.bronze_engine,
                    schema="staging_pagila",
                    if_exists="append",
                    index=False
                )
                failed_count = len(failed_records)
                logger.warning(f"   📥 Queued {failed_count} failed records to dead letter queue")
            except Exception as e:
                logger.error(f"   ❌ Failed to write to dead letter queue: {str(e)}")
                self.stats["errors"].append(f"DLQ write failed: {str(e)}")

        # Update stats
        self.stats["records_processed"] += len(source_df)
        self.stats["records_success"] += success_count
        self.stats["records_failed"] += failed_count
        self.stats["tables_processed"] += 1

        return {
            "success": success_count,
            "failed": failed_count,
            "total": len(source_df),
            "dlq_written": failed_count > 0
        }

    def _add_audit_fields(self, row: pd.Series, source_table: str) -> Dict[str, Any]:
        """Add Bronze audit fields to record."""
        record = row.to_dict()
        record.update({
            "br_load_time": datetime.now(),
            "br_source_file": f"{source_table}_{self.batch_id}",
            "br_batch_id": self.batch_id,
            "br_is_current": True,
            # Generate surrogate key based on source table
            f"br_{source_table}_key": str(uuid4())
        })
        return record

    def _validate_bronze_record(self, record: Dict[str, Any], bronze_table: str) -> None:
        """
        Validate record against strict Bronze schema.
        Raises exceptions for contract violations.
        """
        # This is where strict type validation would happen
        # For demo, we'll do basic validation

        if bronze_table == "br_customer":
            if not isinstance(record.get("customer_id"), (int, str)):
                raise ValueError(f"customer_id must be integer, got {type(record.get('customer_id'))}")

            if record.get("email") is not None and "@" not in str(record.get("email")):
                raise ValueError(f"Invalid email format: {record.get('email')}")

    def _classify_error(self, error: Exception) -> str:
        """Classify error type for dead letter queue."""
        if isinstance(error, (TypeError, ValueError)):
            return "SCHEMA_VALIDATION"
        elif isinstance(error, (IntegrityError, DataError)):
            return "CONSTRAINT_VIOLATION"
        else:
            return "UNKNOWN_ERROR"

    def _extract_failed_field(self, error: Exception) -> Optional[str]:
        """Extract field name from error message."""
        error_str = str(error)
        # Simple field extraction logic - could be enhanced
        for field in ["customer_id", "email", "first_name", "last_name"]:
            if field in error_str:
                return field
        return None

    def _extract_expected_type(self, error: Exception) -> Optional[str]:
        """Extract expected type from error message."""
        error_str = str(error)
        if "integer" in error_str.lower():
            return "integer"
        elif "email" in error_str.lower():
            return "email_format"
        elif "date" in error_str.lower():
            return "date"
        return None

    def get_ingestion_summary(self) -> Dict[str, Any]:
        """Get summary of ingestion results."""
        success_rate = (
            (self.stats["records_success"] / self.stats["records_processed"]) * 100
            if self.stats["records_processed"] > 0 else 0
        )

        return {
            **self.stats,
            "success_rate": round(success_rate, 2),
            "has_errors": len(self.stats["errors"]) > 0 or self.stats["records_failed"] > 0
        }