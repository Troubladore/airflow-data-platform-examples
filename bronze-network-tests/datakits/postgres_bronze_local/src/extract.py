#!/usr/bin/env python3
"""
Bronze Layer Postgres Extraction for Local/Container Databases

This prototype demonstrates extracting data from local Postgres databases
(including container-to-container and host networking scenarios).
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

class LocalPostgresBronzeExtractor:
    """Extract data from local Postgres to Bronze layer"""

    def __init__(self, config=None):
        """Initialize extractor with configuration"""
        self.config = config or self._get_default_config()
        self.bronze_path = Path(self.config.get('bronze_path', '/data/bronze'))
        self.bronze_path.mkdir(parents=True, exist_ok=True)

    def _get_default_config(self):
        """Get default configuration from environment"""
        return {
            'host': os.getenv('POSTGRES_HOST', 'host.docker.internal'),
            'port': os.getenv('POSTGRES_PORT', '5432'),
            'database': os.getenv('POSTGRES_DB', 'pagila'),
            'user': os.getenv('POSTGRES_USER', 'postgres'),
            'password': os.getenv('POSTGRES_PASSWORD', 'postgres'),
            'bronze_path': os.getenv('BRONZE_PATH', '/data/bronze'),
            'source_system': 'pagila_local'
        }

    def test_network_connectivity(self):
        """Test various network connectivity patterns"""
        logger.info("Testing network connectivity patterns...")

        test_hosts = [
            ('host.docker.internal', 'Host machine from container'),
            ('localhost', 'Container localhost'),
            ('postgres', 'Docker Compose service name'),
            (self.config['host'], 'Configured host')
        ]

        results = {}
        for host, description in test_hosts:
            logger.info(f"Testing {description} ({host})...")

            # Try to resolve the hostname
            import socket
            try:
                ip = socket.gethostbyname(host)
                results[host] = {
                    'description': description,
                    'resolved': True,
                    'ip': ip
                }
                logger.info(f"  ✓ Resolved to {ip}")
            except socket.gaierror as e:
                results[host] = {
                    'description': description,
                    'resolved': False,
                    'error': str(e)
                }
                logger.warning(f"  ✗ Could not resolve: {e}")

            # Try to connect to Postgres port
            if results[host].get('resolved'):
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(2)
                    result = sock.connect_ex((host, int(self.config['port'])))
                    sock.close()

                    if result == 0:
                        results[host]['port_open'] = True
                        logger.info(f"  ✓ Port {self.config['port']} is open")
                    else:
                        results[host]['port_open'] = False
                        logger.warning(f"  ✗ Port {self.config['port']} is closed")
                except Exception as e:
                    results[host]['port_open'] = False
                    results[host]['port_error'] = str(e)
                    logger.warning(f"  ✗ Port check failed: {e}")

        return results

    def get_connection(self, host_override=None):
        """Create Postgres connection with standard auth"""
        host = host_override or self.config['host']
        logger.info(f"Connecting to {host}:{self.config['port']}/{self.config['database']}")

        conn_params = {
            'host': host,
            'port': self.config['port'],
            'database': self.config['database'],
            'user': self.config['user'],
            'password': self.config['password']
        }

        try:
            conn = psycopg2.connect(**conn_params)
            logger.info("Successfully connected")

            # Verify the connection
            with conn.cursor() as cur:
                cur.execute("SELECT current_user, current_database(), inet_server_addr(), inet_server_port()")
                user, db, server_addr, server_port = cur.fetchone()
                logger.info(f"Connected as: {user} to {db} at {server_addr}:{server_port}")

            return conn
        except Exception as e:
            logger.error(f"Failed to connect to {host}: {e}")
            raise

    def extract_table(self, table_name, limit=100, host_override=None):
        """Extract data from a table to Bronze layer"""
        logger.info(f"Extracting table: {table_name}")

        conn = None
        try:
            conn = self.get_connection(host_override)

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
            df['bronze_source_host'] = host_override or self.config['host']
            df['bronze_extraction_method'] = 'full_snapshot'

            # Write to Bronze storage
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_dir = self.bronze_path / self.config['source_system'] / table_name
            output_dir.mkdir(parents=True, exist_ok=True)

            # Write as both Parquet and JSON
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
                'json_path': str(json_path),
                'host_used': host_override or self.config['host']
            }

        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'host_attempted': host_override or self.config['host']
            }
        finally:
            if conn:
                conn.close()

    def test_all_connectivity_patterns(self):
        """Test all network patterns and find what works"""
        logger.info("Testing all connectivity patterns...")

        # First test network connectivity
        network_results = self.test_network_connectivity()

        # Try to connect to each reachable host
        connection_results = {}
        for host, info in network_results.items():
            if info.get('port_open'):
                logger.info(f"Attempting database connection to {host}...")
                try:
                    conn = self.get_connection(host_override=host)

                    # Get database info
                    with conn.cursor(cursor_factory=RealDictCursor) as cur:
                        cur.execute("""
                            SELECT current_database() as database,
                                   current_user as user,
                                   version() as version
                        """)
                        db_info = cur.fetchone()

                        # Check for Pagila tables
                        cur.execute("""
                            SELECT COUNT(*) as table_count
                            FROM information_schema.tables
                            WHERE table_schema = 'public'
                        """)
                        table_count = cur.fetchone()['table_count']

                        # Check if this looks like Pagila
                        cur.execute("""
                            SELECT EXISTS(
                                SELECT 1 FROM information_schema.tables
                                WHERE table_name IN ('film', 'actor', 'customer')
                            ) as is_pagila
                        """)
                        is_pagila = cur.fetchone()['is_pagila']

                    conn.close()

                    connection_results[host] = {
                        'success': True,
                        'database': db_info['database'],
                        'user': db_info['user'],
                        'version': db_info['version'][:50],
                        'table_count': table_count,
                        'is_pagila': is_pagila
                    }
                    logger.info(f"  ✓ Connected successfully (Pagila: {is_pagila})")

                except Exception as e:
                    connection_results[host] = {
                        'success': False,
                        'error': str(e)
                    }
                    logger.warning(f"  ✗ Connection failed: {e}")

        return {
            'network_tests': network_results,
            'connection_tests': connection_results
        }


def main():
    """Main entry point for testing"""
    extractor = LocalPostgresBronzeExtractor()

    # Test all connectivity patterns
    logger.info("=" * 60)
    logger.info("TESTING LOCAL POSTGRES CONNECTIVITY PATTERNS")
    logger.info("=" * 60)

    test_results = extractor.test_all_connectivity_patterns()
    print(json.dumps(test_results, indent=2))

    # Find working connections with Pagila
    working_hosts = []
    for host, result in test_results['connection_tests'].items():
        if result.get('success') and result.get('is_pagila'):
            working_hosts.append(host)
            logger.info(f"Found Pagila database at: {host}")

    if not working_hosts:
        logger.warning("No Pagila databases found!")
        logger.info("Attempting to extract from any available database...")
        # Try any successful connection
        for host, result in test_results['connection_tests'].items():
            if result.get('success'):
                working_hosts.append(host)
                break

    # Extract sample data from first working host
    if working_hosts:
        host = working_hosts[0]
        logger.info("=" * 60)
        logger.info(f"EXTRACTING SAMPLE DATA FROM {host}")
        logger.info("=" * 60)

        # Try common Pagila tables
        test_tables = ['film', 'actor', 'customer', 'rental', 'payment']
        for table in test_tables:
            try:
                result = extractor.extract_table(table, limit=10, host_override=host)
                print(json.dumps(result, indent=2))
                if result['success']:
                    break
            except Exception as e:
                logger.warning(f"Table {table} not found: {e}")

    logger.info("=" * 60)
    logger.info("TEST COMPLETE")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()