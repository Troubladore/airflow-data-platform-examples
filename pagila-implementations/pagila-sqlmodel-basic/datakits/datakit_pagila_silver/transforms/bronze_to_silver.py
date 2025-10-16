"""
Silver Layer: Bronze to Silver Transformation with Quarantine System

Implements strict type validation and business rules on Bronze data,
quarantining failed records to sl_transformation_errors table following
industry standard patterns.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from uuid import UUID, uuid4

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


logger = logging.getLogger(__name__)


class BronzeToSilverTransformer:
    """Transforms Bronze layer data to Silver layer with strict validation."""

    def __init__(self, bronze_conn_string: str, silver_conn_string: str, batch_id: str):
        """
        Initialize transformer with database connections.

        Args:
            bronze_conn_string: Bronze database connection
            silver_conn_string: Silver target database connection
            batch_id: Unique batch identifier for this run
        """
        self.bronze_engine = create_engine(bronze_conn_string)
        self.silver_engine = create_engine(silver_conn_string)
        self.batch_id = batch_id
        self.transformation_stats = {
            "tables_processed": 0,
            "total_records_processed": 0,
            "total_records_promoted": 0,
            "total_records_quarantined": 0,
            "errors": []
        }

    def transform_br_customer_to_silver(self) -> Dict[str, Any]:
        """Transform Bronze customer records to Silver layer with strict validation."""
        logger.info("🥈 Transforming br_customer to Silver...")

        bronze_query = """
        SELECT
            br_customer_key,
            customer_id, store_id, first_name, last_name, email,
            address_id, activebool, create_date, last_update, active,
            br_load_time, br_batch_id, br_record_hash
        FROM staging_pagila.br_customer
        WHERE br_is_current = true
        ORDER BY br_customer_key
        """

        return self._transform_table_to_silver(
            bronze_query=bronze_query,
            bronze_table="br_customer",
            silver_table="sl_customer",
            validation_rules=self._validate_customer_record
        )

    def _validate_customer_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply strict validation rules to customer record.

        Returns:
            Dict with 'valid', 'clean_record', 'error_category', 'error_message'
        """
        try:
            clean_record = {}

            # Validate customer_id (required int)
            if not record.get('customer_id'):
                return {
                    'valid': False,
                    'error_category': 'MISSING_FIELD',
                    'error_message': 'customer_id is required but missing',
                    'failed_field': 'customer_id'
                }

            try:
                clean_record['customer_id'] = int(record['customer_id'])
            except (ValueError, TypeError):
                return {
                    'valid': False,
                    'error_category': 'DATA_TYPE',
                    'error_message': f'customer_id must be integer, got: {record["customer_id"]}',
                    'failed_field': 'customer_id',
                    'actual_value': str(record['customer_id'])
                }

            # Validate store_id (required int)
            if not record.get('store_id'):
                return {
                    'valid': False,
                    'error_category': 'MISSING_FIELD',
                    'error_message': 'store_id is required but missing',
                    'failed_field': 'store_id'
                }

            try:
                clean_record['store_id'] = int(record['store_id'])
            except (ValueError, TypeError):
                return {
                    'valid': False,
                    'error_category': 'DATA_TYPE',
                    'error_message': f'store_id must be integer, got: {record["store_id"]}',
                    'failed_field': 'store_id',
                    'actual_value': str(record['store_id'])
                }

            # Validate first_name (required string, max 100 chars)
            if not record.get('first_name'):
                return {
                    'valid': False,
                    'error_category': 'MISSING_FIELD',
                    'error_message': 'first_name is required but missing',
                    'failed_field': 'first_name'
                }

            first_name = str(record['first_name']).strip()
            if len(first_name) > 100:
                return {
                    'valid': False,
                    'error_category': 'BUSINESS_RULE',
                    'error_message': 'first_name exceeds 100 character limit',
                    'failed_field': 'first_name',
                    'actual_value': first_name[:50] + "..." if len(first_name) > 50 else first_name
                }
            clean_record['first_name'] = first_name

            # Validate last_name (required string, max 100 chars)
            if not record.get('last_name'):
                return {
                    'valid': False,
                    'error_category': 'MISSING_FIELD',
                    'error_message': 'last_name is required but missing',
                    'failed_field': 'last_name'
                }

            last_name = str(record['last_name']).strip()
            if len(last_name) > 100:
                return {
                    'valid': False,
                    'error_category': 'BUSINESS_RULE',
                    'error_message': 'last_name exceeds 100 character limit',
                    'failed_field': 'last_name',
                    'actual_value': last_name[:50] + "..." if len(last_name) > 50 else last_name
                }
            clean_record['last_name'] = last_name

            # Validate email (required, basic format check)
            if not record.get('email'):
                return {
                    'valid': False,
                    'error_category': 'MISSING_FIELD',
                    'error_message': 'email is required but missing',
                    'failed_field': 'email'
                }

            email = str(record['email']).strip().lower()
            if '@' not in email or '.' not in email.split('@')[1]:
                return {
                    'valid': False,
                    'error_category': 'BUSINESS_RULE',
                    'error_message': 'email format is invalid',
                    'failed_field': 'email',
                    'actual_value': email
                }
            clean_record['email'] = email

            # Validate address_id (optional int)
            if record.get('address_id'):
                try:
                    clean_record['address_id'] = int(record['address_id'])
                except (ValueError, TypeError):
                    return {
                        'valid': False,
                        'error_category': 'DATA_TYPE',
                        'error_message': f'address_id must be integer, got: {record["address_id"]}',
                        'failed_field': 'address_id',
                        'actual_value': str(record['address_id'])
                    }
            else:
                clean_record['address_id'] = None

            # Validate activebool (boolean)
            if record.get('activebool') is not None:
                activebool_val = str(record['activebool']).lower()
                if activebool_val in ('true', '1', 'yes', 't'):
                    clean_record['activebool'] = True
                elif activebool_val in ('false', '0', 'no', 'f'):
                    clean_record['activebool'] = False
                else:
                    return {
                        'valid': False,
                        'error_category': 'DATA_TYPE',
                        'error_message': f'activebool must be boolean-like, got: {record["activebool"]}',
                        'failed_field': 'activebool',
                        'actual_value': str(record['activebool'])
                    }
            else:
                clean_record['activebool'] = True  # Default

            # Validate dates - parse create_date and last_update
            for date_field in ['create_date', 'last_update']:
                if record.get(date_field):
                    try:
                        # Try to parse as datetime
                        if isinstance(record[date_field], str):
                            clean_record[date_field] = datetime.fromisoformat(record[date_field].replace('Z', '+00:00'))
                        else:
                            clean_record[date_field] = record[date_field]  # Already datetime
                    except (ValueError, TypeError):
                        return {
                            'valid': False,
                            'error_category': 'DATA_TYPE',
                            'error_message': f'{date_field} is not a valid datetime',
                            'failed_field': date_field,
                            'actual_value': str(record[date_field])
                        }
                else:
                    clean_record[date_field] = None

            # Validate active (optional int, 0 or 1)
            if record.get('active') is not None:
                try:
                    active_val = int(record['active'])
                    if active_val not in (0, 1):
                        return {
                            'valid': False,
                            'error_category': 'BUSINESS_RULE',
                            'error_message': 'active must be 0 or 1',
                            'failed_field': 'active',
                            'actual_value': str(record['active'])
                        }
                    clean_record['active'] = active_val
                except (ValueError, TypeError):
                    return {
                        'valid': False,
                        'error_category': 'DATA_TYPE',
                        'error_message': f'active must be integer, got: {record["active"]}',
                        'failed_field': 'active',
                        'actual_value': str(record['active'])
                    }
            else:
                clean_record['active'] = 1  # Default

            # Add Silver audit fields
            clean_record.update({
                'sl_customer_key': str(uuid4()),
                'br_source_key': record['br_customer_key'],
                'sl_load_time': datetime.now(),
                'sl_batch_id': self.batch_id
            })

            return {'valid': True, 'clean_record': clean_record}

        except Exception as e:
            return {
                'valid': False,
                'error_category': 'SYSTEM_ERROR',
                'error_message': f'Validation failed with system error: {str(e)}',
                'failed_field': None
            }

    def _transform_table_to_silver(
        self,
        bronze_query: str,
        bronze_table: str,
        silver_table: str,
        validation_rules
    ) -> Dict[str, Any]:
        """
        Generic method to transform Bronze table to Silver with quarantine.

        Args:
            bronze_query: SQL query to read Bronze data
            bronze_table: Bronze table name for logging
            silver_table: Target Silver table name
            validation_rules: Function to validate and clean records

        Returns:
            Dict with transformation results and statistics
        """
        try:
            # Read Bronze data
            logger.info(f"   📊 Reading from Bronze table: {bronze_table}")
            bronze_df = pd.read_sql(bronze_query, self.bronze_engine)

            if len(bronze_df) == 0:
                logger.warning(f"   ⚠️ No records found in {bronze_table}")
                return {"success": False, "records": 0, "error": "No records found"}

            logger.info(f"   ✅ Read {len(bronze_df)} records from {bronze_table}")

            # Process records with validation
            clean_records = []
            quarantine_records = []

            for _, row in bronze_df.iterrows():
                record_dict = row.to_dict()
                validation_result = validation_rules(record_dict)

                if validation_result['valid']:
                    clean_records.append(validation_result['clean_record'])
                else:
                    # Create quarantine record
                    quarantine_record = {
                        'error_id': str(uuid4()),
                        'br_source_key': record_dict.get('br_customer_key'),  # Will be generalized
                        'source_table': bronze_table,
                        'target_table': silver_table,
                        'batch_id': self.batch_id,
                        'bronze_record_json': json.dumps(record_dict, default=str),
                        'error_category': validation_result.get('error_category', 'UNKNOWN'),
                        'error_message': validation_result.get('error_message', 'Unknown error'),
                        'failed_field': validation_result.get('failed_field'),
                        'expected_value': validation_result.get('expected_value'),
                        'actual_value': validation_result.get('actual_value'),
                        'transformation_rule': f'{bronze_table}_to_{silver_table}_validation',
                        'severity': 'MEDIUM',  # Can be enhanced with rule-based severity
                        'remediation_status': 'PENDING',
                        'created_at': datetime.now(),
                        'retry_count': 0,
                        'alert_sent': False
                    }
                    quarantine_records.append(quarantine_record)

            # Load clean records to Silver
            if clean_records:
                clean_df = pd.DataFrame(clean_records)
                logger.info(f"   💎 Loading {len(clean_df)} clean records to silver_pagila.{silver_table}...")

                clean_df.to_sql(
                    silver_table,
                    self.silver_engine,
                    schema="silver_pagila",
                    if_exists="append",
                    index=False,
                    method='multi'
                )
                logger.info(f"   ✅ Successfully loaded {len(clean_df)} clean records")

            # Load quarantine records to error table
            if quarantine_records:
                quarantine_df = pd.DataFrame(quarantine_records)
                logger.info(f"   📥 Quarantining {len(quarantine_df)} failed records...")

                quarantine_df.to_sql(
                    "sl_transformation_errors",
                    self.silver_engine,
                    schema="silver_pagila",
                    if_exists="append",
                    index=False,
                    method='multi'
                )
                logger.info(f"   ⚠️ Quarantined {len(quarantine_df)} failed records for remediation")

            # Update stats
            self.transformation_stats["tables_processed"] += 1
            self.transformation_stats["total_records_processed"] += len(bronze_df)
            self.transformation_stats["total_records_promoted"] += len(clean_records)
            self.transformation_stats["total_records_quarantined"] += len(quarantine_records)

            success_rate = (len(clean_records) / len(bronze_df)) * 100
            logger.info(f"   📊 Success rate: {success_rate:.1f}% ({len(clean_records)}/{len(bronze_df)})")

            return {
                "success": True,
                "bronze_records": len(bronze_df),
                "clean_records": len(clean_records),
                "quarantined_records": len(quarantine_records),
                "success_rate": success_rate,
                "table": silver_table
            }

        except SQLAlchemyError as e:
            error_msg = f"Database error transforming {bronze_table}: {str(e)}"
            logger.error(f"   ❌ {error_msg}")
            self.transformation_stats["errors"].append(error_msg)
            return {"success": False, "error": error_msg, "records": 0}

        except Exception as e:
            error_msg = f"Unexpected error transforming {bronze_table}: {str(e)}"
            logger.error(f"   ❌ {error_msg}")
            self.transformation_stats["errors"].append(error_msg)
            return {"success": False, "error": error_msg, "records": 0}

    def transform_all_tables(self) -> Dict[str, Any]:
        """Transform all Bronze tables to Silver layer with quarantine."""
        logger.info(f"🥈 SILVER TRANSFORMATION STARTED - Batch ID: {self.batch_id}")

        # Define transformation methods (can be expanded)
        transformation_methods = [
            ("br_customer", self.transform_br_customer_to_silver),
            # Future: ("br_film", self.transform_br_film_to_silver),
            # Future: ("br_rental", self.transform_br_rental_to_silver)
        ]

        results = {}

        for table_name, transformation_method in transformation_methods:
            try:
                result = transformation_method()
                results[table_name] = result

                if result["success"]:
                    logger.info(
                        f"   ✅ {table_name}: {result['clean_records']} promoted, "
                        f"{result['quarantined_records']} quarantined"
                    )
                else:
                    logger.error(f"   ❌ {table_name}: {result.get('error', 'Unknown error')}")

            except Exception as e:
                error_msg = f"Failed to transform {table_name}: {str(e)}"
                logger.error(f"   ❌ {error_msg}")
                results[table_name] = {"success": False, "error": error_msg}
                self.transformation_stats["errors"].append(error_msg)

        # Generate summary
        successful_tables = sum(1 for r in results.values() if r.get("success", False))
        total_tables = len(transformation_methods)

        logger.info(f"🥈 SILVER TRANSFORMATION COMPLETE:")
        logger.info(f"   📊 Tables: {successful_tables}/{total_tables} successful")
        logger.info(f"   💎 Records promoted: {self.transformation_stats['total_records_promoted']}")
        logger.info(f"   📥 Records quarantined: {self.transformation_stats['total_records_quarantined']}")

        if self.transformation_stats["errors"]:
            logger.warning(f"   ⚠️ Errors: {len(self.transformation_stats['errors'])} issues encountered")

        overall_success_rate = (
            (self.transformation_stats['total_records_promoted'] /
             self.transformation_stats['total_records_processed']) * 100
            if self.transformation_stats['total_records_processed'] > 0 else 0
        )

        return {
            "batch_id": self.batch_id,
            "success_rate": overall_success_rate,
            "tables_processed": successful_tables,
            "total_records_processed": self.transformation_stats["total_records_processed"],
            "total_records_promoted": self.transformation_stats["total_records_promoted"],
            "total_records_quarantined": self.transformation_stats["total_records_quarantined"],
            "errors": self.transformation_stats["errors"],
            "results": results
        }

    def close_connections(self):
        """Close database connections."""
        if hasattr(self.bronze_engine, 'dispose'):
            self.bronze_engine.dispose()
        if hasattr(self.silver_engine, 'dispose'):
            self.silver_engine.dispose()


def transform_bronze_to_silver_tables(
    bronze_conn: str,
    silver_conn: str,
    batch_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main function to transform Bronze data to Silver layer with quarantine.

    Args:
        bronze_conn: Bronze database connection string
        silver_conn: Silver database connection string
        batch_id: Optional batch ID (auto-generated if not provided)

    Returns:
        Transformation results and statistics
    """
    if batch_id is None:
        batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    transformer = None
    try:
        transformer = BronzeToSilverTransformer(bronze_conn, silver_conn, batch_id)
        return transformer.transform_all_tables()
    finally:
        if transformer:
            transformer.close_connections()