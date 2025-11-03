"""
Bronze Layer Postgres Extraction for Local Testing

This is now a thin wrapper around framework base classes,
without Kerberos authentication for local development.
"""

import logging
import json
import sys
from pathlib import Path
import pandas as pd

# Add framework to path for imports
sys.path.insert(0, '/home/emaynard/repos/airflow-data-platform/sqlmodel-framework/src')

# Import from framework
from sqlmodel_framework.base.connectors import PostgresConnector, PostgresConfig
from sqlmodel_framework.base.loaders import BronzeIngestionPipeline

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class LocalPagilaBronzeExtractor(BronzeIngestionPipeline):
    """Extract Pagila data to Bronze layer for local testing"""

    def __init__(self, connector: PostgresConnector, bronze_path: Path):
        super().__init__(connector, bronze_path)
        self.source_system = 'pagila_local'

    def test_connectivity(self):
        """Test connectivity using framework connector"""
        logger.info("Testing local connectivity...")

        # Framework handles connection testing
        if not self.connector.test_connection():
            return {
                'success': False,
                'error': 'Connection test failed'
            }

        # Get tables using framework method
        try:
            tables = self.connector.get_tables(schema='public')

            # Check for Pagila tables
            pagila_tables = ['film', 'actor', 'customer']
            is_pagila = all(t in tables for t in pagila_tables)

            return {
                'success': True,
                'tables_found': tables[:10],
                'is_pagila': is_pagila
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def extract_table(self, table_name: str, host_override: str = None, limit: int = 100) -> dict:
        """Extract table using framework ingestion pipeline

        Args:
            table_name: Name of table to extract
            host_override: Override host name in metadata (for different environments)
            limit: Maximum rows to extract
        """
        logger.info(f"Extracting table: {table_name}")

        try:
            # Extract data using framework connection context
            with self.connector.connection_context() as conn:
                query = f"SELECT * FROM {table_name} LIMIT {limit}"
                df = pd.read_sql(query, conn)

            logger.info(f"Extracted {len(df)} rows from {table_name}")

            # Use host override if provided, otherwise use config host
            source_host = host_override if host_override else self.connector.config.host

            # Add Bronze metadata using framework method
            df = self.add_bronze_metadata(
                df,
                source_system=self.source_system,
                source_table=table_name,
                source_host=source_host,
                extraction_method='full_snapshot'
            )

            # Write using framework method
            paths = self.write_bronze(
                df,
                source_system=self.source_system,
                table_name=table_name,
                formats=['parquet', 'json']
            )

            return {
                'success': True,
                'rows_extracted': len(df),
                'parquet_path': paths['parquet'],
                'json_path': paths['json']
            }

        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }


def main():
    """Main entry point for testing"""
    # Configure using framework config class WITHOUT Kerberos
    config = PostgresConfig(
        host='localhost',
        port=5432,
        database='pagila',
        username='postgres',
        password='postgres',
        use_kerberos=False  # Explicitly disable Kerberos for local
    )

    # Create framework connector
    connector = PostgresConnector(config)

    # Create extractor using framework pipeline
    extractor = LocalPagilaBronzeExtractor(
        connector=connector,
        bronze_path=Path('/data/bronze')
    )

    # Test connectivity
    logger.info("=" * 60)
    logger.info("TESTING LOCAL POSTGRES CONNECTIVITY")
    logger.info("=" * 60)

    conn_result = extractor.test_connectivity()
    print(json.dumps(conn_result, indent=2))

    if not conn_result['success']:
        logger.error("Connectivity test failed!")
        sys.exit(1)

    # Extract sample tables
    logger.info("=" * 60)
    logger.info("EXTRACTING SAMPLE DATA")
    logger.info("=" * 60)

    # Test different host overrides for different environments
    environments = {
        'docker': 'postgres-container',
        'local': 'localhost',
        'kubernetes': 'postgres-service'
    }

    test_tables = ['film', 'actor', 'customer']
    for env_name, host in environments.items():
        logger.info(f"Testing extraction for {env_name} environment...")
        for table in test_tables[:1]:  # Just test first table for each env
            if table in conn_result.get('tables_found', []):
                logger.info(f"Extracting {table} with host override: {host}...")
                result = extractor.extract_table(table, host_override=host, limit=5)
                print(f"{env_name}: {json.dumps(result, indent=2)}")

    logger.info("=" * 60)
    logger.info("TEST COMPLETE")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()