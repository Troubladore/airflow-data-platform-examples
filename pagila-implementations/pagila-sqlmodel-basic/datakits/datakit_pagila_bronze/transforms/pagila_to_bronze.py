"""
Bronze Layer: Pagila Source to Bronze Transformation

Implements actual data extraction from Pagila source database and loading
to Bronze layer tables with audit fields and industry standard patterns.
"""

import hashlib
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from uuid import uuid4

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


logger = logging.getLogger(__name__)


class PagilaToBronzeExtractor:
    """Extracts data from Pagila source and loads to Bronze layer."""

    def __init__(self, source_conn_string: str, bronze_conn_string: str, batch_id: str):
        """
        Initialize extractor with database connections.

        Args:
            source_conn_string: Pagila source database connection
            bronze_conn_string: Bronze target database connection
            batch_id: Unique batch identifier for this run
        """
        self.source_engine = create_engine(source_conn_string)
        self.bronze_engine = create_engine(bronze_conn_string)
        self.batch_id = batch_id
        self.extraction_stats = {
            "tables_processed": 0,
            "total_records_extracted": 0,
            "total_records_loaded": 0,
            "errors": []
        }

    def extract_customer_to_bronze(self) -> Dict[str, Any]:
        """Extract customer table from Pagila to Bronze layer."""
        logger.info("🥉 Extracting customer table to Bronze...")

        source_query = """
        SELECT
            customer_id,
            store_id,
            first_name,
            last_name,
            email,
            address_id,
            activebool,
            create_date,
            last_update,
            active
        FROM public.customer
        ORDER BY customer_id
        """

        return self._extract_table_to_bronze(
            source_query=source_query,
            source_table="customer",
            bronze_table="br_customer"
        )

    def extract_film_to_bronze(self) -> Dict[str, Any]:
        """Extract film table from Pagila to Bronze layer."""
        logger.info("🥉 Extracting film table to Bronze...")

        source_query = """
        SELECT
            film_id,
            title,
            description,
            release_year,
            language_id,
            rental_duration,
            rental_rate,
            length,
            replacement_cost,
            rating,
            special_features,
            last_update
        FROM public.film
        ORDER BY film_id
        """

        return self._extract_table_to_bronze(
            source_query=source_query,
            source_table="film",
            bronze_table="br_film"
        )

    def extract_rental_to_bronze(self) -> Dict[str, Any]:
        """Extract rental table from Pagila to Bronze layer."""
        logger.info("🥉 Extracting rental table to Bronze...")

        source_query = """
        SELECT
            rental_id,
            rental_date,
            inventory_id,
            customer_id,
            return_date,
            staff_id,
            last_update
        FROM public.rental
        ORDER BY rental_id
        """

        return self._extract_table_to_bronze(
            source_query=source_query,
            source_table="rental",
            bronze_table="br_rental"
        )

    def _extract_table_to_bronze(
        self,
        source_query: str,
        source_table: str,
        bronze_table: str
    ) -> Dict[str, Any]:
        """
        Generic method to extract table from source to Bronze.

        Args:
            source_query: SQL query to extract source data
            source_table: Source table name for logging
            bronze_table: Target Bronze table name

        Returns:
            Dict with extraction results and statistics
        """
        try:
            # Extract source data
            logger.info(f"   📊 Reading from source table: {source_table}")
            source_df = pd.read_sql(source_query, self.source_engine)

            if len(source_df) == 0:
                logger.warning(f"   ⚠️ No records found in {source_table}")
                return {"success": False, "records": 0, "error": "No records found"}

            logger.info(f"   ✅ Extracted {len(source_df)} records from {source_table}")

            # Add Bronze audit fields
            bronze_records = []
            for _, row in source_df.iterrows():
                # Convert all source fields to strings (industry standard lenient typing)
                bronze_record = {col: str(val) if val is not None else None
                               for col, val in row.items()}

                # Add Bronze audit fields
                bronze_record.update({
                    f"br_{source_table}_key": str(uuid4()),
                    "br_load_time": datetime.now(),
                    "br_source_file": f"{source_table}_{self.batch_id}",
                    "br_record_hash": self._calculate_record_hash(bronze_record),
                    "br_is_current": True,
                    "br_batch_id": self.batch_id
                })

                bronze_records.append(bronze_record)

            # Load to Bronze table
            bronze_df = pd.DataFrame(bronze_records)

            logger.info(f"   💾 Loading {len(bronze_df)} records to {bronze_table}...")
            bronze_df.to_sql(
                bronze_table,
                self.bronze_engine,
                schema="staging_pagila",
                if_exists="append",  # Industry standard: preserve historical data
                index=False,
                method='multi'  # Batch insert for performance
            )

            logger.info(f"   ✅ Successfully loaded {len(bronze_df)} records to staging_pagila.{bronze_table}")

            # Update stats
            self.extraction_stats["tables_processed"] += 1
            self.extraction_stats["total_records_extracted"] += len(source_df)
            self.extraction_stats["total_records_loaded"] += len(bronze_df)

            return {
                "success": True,
                "source_records": len(source_df),
                "bronze_records": len(bronze_df),
                "table": bronze_table
            }

        except SQLAlchemyError as e:
            error_msg = f"Database error extracting {source_table}: {str(e)}"
            logger.error(f"   ❌ {error_msg}")
            self.extraction_stats["errors"].append(error_msg)
            return {"success": False, "error": error_msg, "records": 0}

        except Exception as e:
            error_msg = f"Unexpected error extracting {source_table}: {str(e)}"
            logger.error(f"   ❌ {error_msg}")
            self.extraction_stats["errors"].append(error_msg)
            return {"success": False, "error": error_msg, "records": 0}

    def _calculate_record_hash(self, record: Dict[str, Any]) -> str:
        """Calculate SHA256 hash of record for change detection."""
        # Remove audit fields from hash calculation
        source_fields = {k: v for k, v in record.items()
                        if not k.startswith('br_')}

        record_json = json.dumps(source_fields, sort_keys=True, default=str)
        return hashlib.sha256(record_json.encode()).hexdigest()

    def extract_all_tables(self) -> Dict[str, Any]:
        """Extract all Pagila tables to Bronze layer."""
        logger.info(f"🥉 BRONZE EXTRACTION STARTED - Batch ID: {self.batch_id}")

        # Define extraction methods
        extraction_methods = [
            ("customer", self.extract_customer_to_bronze),
            ("film", self.extract_film_to_bronze),
            ("rental", self.extract_rental_to_bronze)
        ]

        results = {}

        for table_name, extraction_method in extraction_methods:
            try:
                result = extraction_method()
                results[table_name] = result

                if result["success"]:
                    logger.info(f"   ✅ {table_name}: {result['source_records']} records processed")
                else:
                    logger.error(f"   ❌ {table_name}: {result.get('error', 'Unknown error')}")

            except Exception as e:
                error_msg = f"Failed to extract {table_name}: {str(e)}"
                logger.error(f"   ❌ {error_msg}")
                results[table_name] = {"success": False, "error": error_msg}
                self.extraction_stats["errors"].append(error_msg)

        # Generate summary
        successful_tables = sum(1 for r in results.values() if r.get("success", False))
        total_tables = len(extraction_methods)

        logger.info(f"🥉 BRONZE EXTRACTION COMPLETE:")
        logger.info(f"   📊 Tables: {successful_tables}/{total_tables} successful")
        logger.info(f"   📊 Records: {self.extraction_stats['total_records_loaded']} loaded to Bronze")

        if self.extraction_stats["errors"]:
            logger.warning(f"   ⚠️ Errors: {len(self.extraction_stats['errors'])} issues encountered")

        return {
            "batch_id": self.batch_id,
            "success_rate": (successful_tables / total_tables) * 100,
            "tables_processed": successful_tables,
            "total_records": self.extraction_stats["total_records_loaded"],
            "errors": self.extraction_stats["errors"],
            "results": results
        }

    def close_connections(self):
        """Close database connections."""
        if hasattr(self.source_engine, 'dispose'):
            self.source_engine.dispose()
        if hasattr(self.bronze_engine, 'dispose'):
            self.bronze_engine.dispose()


def extract_pagila_to_bronze_tables(
    source_conn: str,
    bronze_conn: str,
    batch_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main function to extract Pagila data to Bronze layer.

    Args:
        source_conn: Pagila source database connection string
        bronze_conn: Bronze database connection string
        batch_id: Optional batch ID (auto-generated if not provided)

    Returns:
        Extraction results and statistics
    """
    if batch_id is None:
        batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    extractor = None
    try:
        extractor = PagilaToBronzeExtractor(source_conn, bronze_conn, batch_id)
        return extractor.extract_all_tables()
    finally:
        if extractor:
            extractor.close_connections()