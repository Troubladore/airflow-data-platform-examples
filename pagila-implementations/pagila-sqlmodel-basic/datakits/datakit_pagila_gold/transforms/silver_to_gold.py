"""
Gold Layer: Silver to Gold Aggregation and Analytics

Implements dimensional modeling and business intelligence transformations
from Silver layer data to Gold layer analytics tables.
"""

import logging
from datetime import datetime, date
from typing import Dict, List, Any, Optional

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


logger = logging.getLogger(__name__)


class SilverToGoldAggregator:
    """Aggregates Silver layer data to Gold layer for analytics and reporting."""

    def __init__(self, silver_conn_string: str, gold_conn_string: str, batch_id: str):
        """
        Initialize aggregator with database connections.

        Args:
            silver_conn_string: Silver database connection
            gold_conn_string: Gold target database connection
            batch_id: Unique batch identifier for this run
        """
        self.silver_engine = create_engine(silver_conn_string)
        self.gold_engine = create_engine(gold_conn_string)
        self.batch_id = batch_id
        self.aggregation_stats = {
            "objects_processed": 0,
            "total_records_created": 0,
            "errors": []
        }

    def create_dim_customer(self) -> Dict[str, Any]:
        """Create customer dimension table with segmentation and lifetime metrics."""
        logger.info("🥇 Creating dim_customer with customer segmentation...")

        silver_query = """
        SELECT
            sl_customer_key,
            customer_id,
            first_name,
            last_name,
            email,
            activebool,
            active,
            sl_load_time
        FROM silver_pagila.sl_customer
        ORDER BY customer_id
        """

        try:
            # Read Silver customer data
            silver_df = pd.read_sql(silver_query, self.silver_engine)

            if len(silver_df) == 0:
                logger.warning("   ⚠️ No customers found in Silver layer")
                return {"success": False, "records": 0, "error": "No customers found"}

            logger.info(f"   📊 Processing {len(silver_df)} customers for dimension table...")

            # Create dimension records with business enrichment
            dim_records = []

            for _, row in silver_df.iterrows():
                # Basic dimension attributes
                dim_record = {
                    'dim_customer_key': row['sl_customer_key'],
                    'customer_id': row['customer_id'],
                    'first_name': row['first_name'],
                    'last_name': row['last_name'],
                    'full_name': f"{row['first_name']} {row['last_name']}",
                    'email': row['email'],
                    'is_active': bool(row['activebool']) and (row['active'] == 1),

                    # Customer segmentation (business rules)
                    'customer_segment': self._determine_customer_segment(row),
                    'email_domain': row['email'].split('@')[1] if '@' in row['email'] else 'unknown',
                    'name_length_category': self._categorize_name_length(row['first_name'], row['last_name']),

                    # Dimension metadata
                    'effective_date': row['sl_load_time'],
                    'is_current': True,
                    'batch_id': self.batch_id,
                    'created_at': datetime.now()
                }

                dim_records.append(dim_record)

            # Load to Gold dimension table
            dim_df = pd.DataFrame(dim_records)

            logger.info(f"   💎 Loading {len(dim_df)} customer dimension records...")
            dim_df.to_sql(
                "dim_customer",
                self.gold_engine,
                schema="gold_pagila",
                if_exists="append",
                index=False,
                method='multi'
            )

            logger.info(f"   ✅ Created dim_customer: {len(dim_df)} customer dimensions")

            # Update stats
            self.aggregation_stats["objects_processed"] += 1
            self.aggregation_stats["total_records_created"] += len(dim_df)

            return {
                "success": True,
                "silver_records": len(silver_df),
                "gold_records": len(dim_df),
                "table": "dim_customer"
            }

        except SQLAlchemyError as e:
            error_msg = f"Database error creating dim_customer: {str(e)}"
            logger.error(f"   ❌ {error_msg}")
            self.aggregation_stats["errors"].append(error_msg)
            return {"success": False, "error": error_msg, "records": 0}

        except Exception as e:
            error_msg = f"Unexpected error creating dim_customer: {str(e)}"
            logger.error(f"   ❌ {error_msg}")
            self.aggregation_stats["errors"].append(error_msg)
            return {"success": False, "error": error_msg, "records": 0}

    def create_dim_date(self) -> Dict[str, Any]:
        """Create date dimension table with business calendar attributes."""
        logger.info("🥇 Creating dim_date with business calendar...")

        try:
            # Generate date range (2005-2025 to cover typical Pagila timeframes)
            start_date = date(2005, 1, 1)
            end_date = date(2025, 12, 31)

            date_records = []
            current_date = start_date

            while current_date <= end_date:
                date_record = {
                    'date_key': int(current_date.strftime('%Y%m%d')),
                    'full_date': current_date,
                    'year': current_date.year,
                    'quarter': (current_date.month - 1) // 3 + 1,
                    'month': current_date.month,
                    'month_name': current_date.strftime('%B'),
                    'month_abbr': current_date.strftime('%b'),
                    'day': current_date.day,
                    'day_of_week': current_date.weekday() + 1,  # Monday=1
                    'day_name': current_date.strftime('%A'),
                    'day_abbr': current_date.strftime('%a'),
                    'day_of_year': current_date.timetuple().tm_yday,
                    'week_of_year': current_date.isocalendar()[1],

                    # Business calendar attributes
                    'is_weekend': current_date.weekday() >= 5,  # Saturday=5, Sunday=6
                    'is_month_end': (current_date.replace(day=28) + pd.DateOffset(days=4)).day <= 4,
                    'is_quarter_end': current_date.month in [3, 6, 9, 12] and
                                    (current_date.replace(day=28) + pd.DateOffset(days=4)).day <= 4,
                    'is_year_end': current_date.month == 12 and current_date.day == 31,

                    # Season (for business analysis)
                    'season': self._determine_season(current_date.month),

                    'batch_id': self.batch_id,
                    'created_at': datetime.now()
                }

                date_records.append(date_record)

                # Move to next day
                current_date += pd.Timedelta(days=1)

            # Load to Gold dimension table
            dim_df = pd.DataFrame(date_records)

            logger.info(f"   💎 Loading {len(dim_df)} date dimension records...")
            dim_df.to_sql(
                "dim_date",
                self.gold_engine,
                schema="gold_pagila",
                if_exists="append",
                index=False,
                method='multi'
            )

            logger.info(f"   ✅ Created dim_date: {len(dim_df)} date dimensions")

            # Update stats
            self.aggregation_stats["objects_processed"] += 1
            self.aggregation_stats["total_records_created"] += len(dim_df)

            return {
                "success": True,
                "gold_records": len(dim_df),
                "date_range": f"{start_date} to {end_date}",
                "table": "dim_date"
            }

        except Exception as e:
            error_msg = f"Unexpected error creating dim_date: {str(e)}"
            logger.error(f"   ❌ {error_msg}")
            self.aggregation_stats["errors"].append(error_msg)
            return {"success": False, "error": error_msg, "records": 0}

    def create_kpi_customer_summary(self) -> Dict[str, Any]:
        """Create customer KPI summary for business intelligence."""
        logger.info("🥇 Creating kpi_customer_summary for analytics...")

        kpi_query = """
        WITH customer_stats AS (
            SELECT
                COUNT(*) as total_customers,
                COUNT(CASE WHEN is_active = true THEN 1 END) as active_customers,
                COUNT(CASE WHEN is_active = false THEN 1 END) as inactive_customers,
                COUNT(DISTINCT email_domain) as unique_email_domains,
                COUNT(CASE WHEN customer_segment = 'Premium' THEN 1 END) as premium_customers,
                COUNT(CASE WHEN customer_segment = 'Standard' THEN 1 END) as standard_customers,
                COUNT(CASE WHEN customer_segment = 'Basic' THEN 1 END) as basic_customers
            FROM gold_pagila.dim_customer
            WHERE is_current = true
        )
        SELECT * FROM customer_stats
        """

        try:
            # Calculate KPIs from dimension tables
            kpi_df = pd.read_sql(kpi_query, self.gold_engine)

            if len(kpi_df) == 0:
                logger.warning("   ⚠️ No customer dimensions found for KPI calculation")
                return {"success": False, "records": 0, "error": "No customer dimensions found"}

            # Enhance with additional business metrics
            kpi_record = kpi_df.iloc[0].to_dict()
            kpi_record.update({
                'active_customer_rate': (kpi_record['active_customers'] / kpi_record['total_customers']) * 100
                                       if kpi_record['total_customers'] > 0 else 0,
                'premium_customer_rate': (kpi_record['premium_customers'] / kpi_record['total_customers']) * 100
                                        if kpi_record['total_customers'] > 0 else 0,
                'measurement_date': datetime.now().date(),
                'batch_id': self.batch_id,
                'created_at': datetime.now()
            })

            # Load to Gold KPI table
            kpi_summary_df = pd.DataFrame([kpi_record])

            logger.info(f"   💎 Loading customer KPI summary...")
            kpi_summary_df.to_sql(
                "kpi_customer_summary",
                self.gold_engine,
                schema="gold_pagila",
                if_exists="append",
                index=False,
                method='multi'
            )

            logger.info(f"   ✅ Created kpi_customer_summary: {kpi_record['total_customers']} customers analyzed")
            logger.info(f"      📊 Active Rate: {kpi_record['active_customer_rate']:.1f}%")
            logger.info(f"      📊 Premium Rate: {kpi_record['premium_customer_rate']:.1f}%")

            # Update stats
            self.aggregation_stats["objects_processed"] += 1
            self.aggregation_stats["total_records_created"] += 1

            return {
                "success": True,
                "kpi_metrics": kpi_record,
                "table": "kpi_customer_summary"
            }

        except Exception as e:
            error_msg = f"Unexpected error creating kpi_customer_summary: {str(e)}"
            logger.error(f"   ❌ {error_msg}")
            self.aggregation_stats["errors"].append(error_msg)
            return {"success": False, "error": error_msg, "records": 0}

    def _determine_customer_segment(self, customer_record) -> str:
        """Apply business rules to determine customer segment."""
        # Simple segmentation based on email domain and name patterns
        email = customer_record.get('email', '').lower()

        if any(domain in email for domain in ['gmail.com', 'yahoo.com', 'hotmail.com']):
            return 'Standard'  # Consumer email providers
        elif any(domain in email for domain in ['.edu', '.gov', '.org']):
            return 'Premium'   # Institutional emails
        elif len(customer_record.get('first_name', '')) + len(customer_record.get('last_name', '')) > 20:
            return 'Premium'   # Longer names might indicate different demographics
        else:
            return 'Basic'

    def _categorize_name_length(self, first_name: str, last_name: str) -> str:
        """Categorize customers by combined name length for analytics."""
        total_length = len(first_name or '') + len(last_name or '')

        if total_length <= 10:
            return 'Short'
        elif total_length <= 20:
            return 'Medium'
        else:
            return 'Long'

    def _determine_season(self, month: int) -> str:
        """Determine season for business calendar."""
        if month in [12, 1, 2]:
            return 'Winter'
        elif month in [3, 4, 5]:
            return 'Spring'
        elif month in [6, 7, 8]:
            return 'Summer'
        else:  # 9, 10, 11
            return 'Fall'

    def aggregate_all_objects(self) -> Dict[str, Any]:
        """Create all Gold layer objects from Silver data."""
        logger.info(f"🥇 GOLD AGGREGATION STARTED - Batch ID: {self.batch_id}")

        # Define aggregation methods
        aggregation_methods = [
            ("dim_customer", self.create_dim_customer),
            ("dim_date", self.create_dim_date),
            ("kpi_customer_summary", self.create_kpi_customer_summary)
        ]

        results = {}

        for object_name, aggregation_method in aggregation_methods:
            try:
                result = aggregation_method()
                results[object_name] = result

                if result["success"]:
                    logger.info(f"   ✅ {object_name}: {result.get('gold_records', result.get('records', 'N/A'))} records created")
                else:
                    logger.error(f"   ❌ {object_name}: {result.get('error', 'Unknown error')}")

            except Exception as e:
                error_msg = f"Failed to create {object_name}: {str(e)}"
                logger.error(f"   ❌ {error_msg}")
                results[object_name] = {"success": False, "error": error_msg}
                self.aggregation_stats["errors"].append(error_msg)

        # Generate summary
        successful_objects = sum(1 for r in results.values() if r.get("success", False))
        total_objects = len(aggregation_methods)

        logger.info(f"🥇 GOLD AGGREGATION COMPLETE:")
        logger.info(f"   📊 Objects: {successful_objects}/{total_objects} successful")
        logger.info(f"   💎 Records created: {self.aggregation_stats['total_records_created']}")

        if self.aggregation_stats["errors"]:
            logger.warning(f"   ⚠️ Errors: {len(self.aggregation_stats['errors'])} issues encountered")

        return {
            "batch_id": self.batch_id,
            "success_rate": (successful_objects / total_objects) * 100,
            "objects_processed": successful_objects,
            "total_records_created": self.aggregation_stats["total_records_created"],
            "errors": self.aggregation_stats["errors"],
            "results": results
        }

    def close_connections(self):
        """Close database connections."""
        if hasattr(self.silver_engine, 'dispose'):
            self.silver_engine.dispose()
        if hasattr(self.gold_engine, 'dispose'):
            self.gold_engine.dispose()


def aggregate_silver_to_gold_tables(
    silver_conn: str,
    gold_conn: str,
    batch_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main function to aggregate Silver data to Gold layer analytics.

    Args:
        silver_conn: Silver database connection string
        gold_conn: Gold database connection string
        batch_id: Optional batch ID (auto-generated if not provided)

    Returns:
        Aggregation results and statistics
    """
    if batch_id is None:
        batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    aggregator = None
    try:
        aggregator = SilverToGoldAggregator(silver_conn, gold_conn, batch_id)
        return aggregator.aggregate_all_objects()
    finally:
        if aggregator:
            aggregator.close_connections()