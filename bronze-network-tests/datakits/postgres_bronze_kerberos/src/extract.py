#!/usr/bin/env python3
"""
Bronze Layer Postgres Extraction with Kerberos Authentication

This prototype demonstrates extracting data from a remote Postgres database
(Pagila) using Kerberos/GSSAPI authentication within a Docker container.
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PostgresBronzeExtractor:
    """Extract data from Postgres to Bronze layer with Kerberos auth"""

    def __init__(self, config=None):
        """Initialize extractor with configuration"""
        self.config = config or self._get_default_config()
        self.bronze_path = Path(self.config.get('bronze_path', '/data/bronze'))
        self.bronze_path.mkdir(parents=True, exist_ok=True)

    def _get_default_config(self):
        """Get default configuration from environment"""
        return {
            'host': os.getenv('POSTGRES_HOST', 'sqlpg.eruditis.lab'),
            'port': os.getenv('POSTGRES_PORT', '5432'),
            'database': os.getenv('POSTGRES_DB', 'pagila'),
            'gssencmode': os.getenv('POSTGRES_GSSENCMODE', 'require'),
            'bronze_path': os.getenv('BRONZE_PATH', '/data/bronze'),
            'source_system': 'pagila_kerberos'
        }

    def test_kerberos_ticket(self):
        """Verify Kerberos ticket is available"""
        logger.info("Checking for Kerberos ticket...")

        # Check if credential cache exists
        krb5_cache = os.getenv('KRB5CCNAME', '')
        if not krb5_cache:
            logger.warning("KRB5CCNAME not set")
            return False

        # Run klist to verify ticket
        import subprocess
        try:
            result = subprocess.run(['klist'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("Kerberos ticket found:")
                logger.info(result.stdout)
                return True
            else:
                logger.error("No valid Kerberos ticket found")
                return False
        except FileNotFoundError:
            logger.error("klist command not found - is Kerberos installed?")
            return False

    def get_connection(self):
        """Create Postgres connection with Kerberos"""
        logger.info(f"Connecting to {self.config['host']}:{self.config['port']}/{self.config['database']}")

        # Connection string for Kerberos auth
        # Note: With Kerberos, we don't need username/password
        conn_params = {
            'host': self.config['host'],
            'port': self.config['port'],
            'database': self.config['database'],
            'gssencmode': self.config['gssencmode'],
            # Kerberos will use the ticket to authenticate
        }

        try:
            conn = psycopg2.connect(**conn_params)
            logger.info("Successfully connected with Kerberos authentication")

            # Verify the connection and user
            with conn.cursor() as cur:
                cur.execute("SELECT current_user, current_database(), version()")
                user, db, version = cur.fetchone()
                logger.info(f"Connected as: {user} to database: {db}")
                logger.info(f"PostgreSQL version: {version[:50]}...")

            return conn
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            raise

    def extract_table(self, table_name, limit=100):
        """Extract data from a table to Bronze layer"""
        logger.info(f"Extracting table: {table_name}")

        conn = None
        try:
            conn = self.get_connection()

            # Query with limit for testing
            query = f"SELECT * FROM {table_name} LIMIT {limit}"
            logger.info(f"Executing: {query}")

            # Read into DataFrame
            df = pd.read_sql(query, conn)
            logger.info(f"Extracted {len(df)} rows from {table_name}")

            # Add Bronze metadata
            df['bronze_load_timestamp'] = datetime.now().isoformat()
            df['bronze_source_system'] = self.config['source_system']
            df['bronze_source_table'] = table_name
            df['bronze_extraction_method'] = 'full_snapshot'

            # Write to Bronze storage
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_dir = self.bronze_path / self.config['source_system'] / table_name
            output_dir.mkdir(parents=True, exist_ok=True)

            # Write as both Parquet and JSON for testing
            parquet_path = output_dir / f"{timestamp}.parquet"
            json_path = output_dir / f"{timestamp}.json"

            df.to_parquet(parquet_path)
            df.to_json(json_path, orient='records', date_format='iso')

            logger.info(f"Written to: {parquet_path}")
            logger.info(f"Written to: {json_path}")

            return {
                'success': True,
                'rows_extracted': len(df),
                'parquet_path': str(parquet_path),
                'json_path': str(json_path)
            }

        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            if conn:
                conn.close()

    def test_connectivity(self):
        """Test basic connectivity without extracting data"""
        logger.info("Testing connectivity...")

        # First check Kerberos
        if not self.test_kerberos_ticket():
            return {
                'success': False,
                'error': 'No valid Kerberos ticket'
            }

        # Try to connect
        try:
            conn = self.get_connection()

            # Get some basic info
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Check available tables
                cur.execute("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                    LIMIT 10
                """)
                tables = [row['table_name'] for row in cur.fetchall()]

                # Get row counts for a few tables
                table_info = {}
                for table in tables[:3]:
                    cur.execute(f"SELECT COUNT(*) as count FROM {table}")
                    table_info[table] = cur.fetchone()['count']

            conn.close()

            return {
                'success': True,
                'tables_found': tables,
                'sample_counts': table_info
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


def main():
    """Main entry point for testing"""
    extractor = PostgresBronzeExtractor()

    # Test connectivity first
    logger.info("=" * 60)
    logger.info("TESTING KERBEROS POSTGRES CONNECTIVITY")
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

    test_tables = ['film', 'actor', 'customer']
    for table in test_tables:
        if table in conn_result.get('tables_found', []):
            logger.info(f"Extracting {table}...")
            result = extractor.extract_table(table, limit=10)
            print(json.dumps(result, indent=2))

    logger.info("=" * 60)
    logger.info("TEST COMPLETE")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()