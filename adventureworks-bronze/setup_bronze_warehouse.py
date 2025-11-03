#!/usr/bin/env python
"""
Setup script for Bronze Warehouse database

This script creates the bronze_warehouse database and schema on PostgreSQL.
It handles both Kerberos and password authentication.

Usage:
    python setup_bronze_warehouse.py
"""

import sys
import subprocess
from pathlib import Path
import yaml

# Add the package to path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, '/home/emaynard/repos/airflow-data-platform/sqlmodel-framework/src')

from sqlalchemy import create_engine, text
from sqlmodel import SQLModel, Session
from bronze_datakits_adventureworkslt.models import ProductCategoryBronze


def load_config():
    """Load configuration from config.yaml"""
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


def get_kerberos_username():
    """Extract username from Kerberos ticket"""
    try:
        result = subprocess.run(['klist'], capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if 'Default principal:' in line:
                    principal = line.split(':')[1].strip()
                    username = principal.split('@')[0]
                    return username
    except Exception:
        pass
    return None


def create_database(config):
    """Create bronze_warehouse database if it doesn't exist"""
    target = config['target']

    print("=" * 80)
    print("Step 1: Creating bronze_warehouse database")
    print("=" * 80)

    # Connect to postgres database to create bronze_warehouse
    if target.get('use_kerberos', True):
        username = get_kerberos_username()
        if not username:
            print("ERROR: No Kerberos ticket found. Run 'kinit' first.")
            sys.exit(1)

        print(f"Using Kerberos authentication as: {username}")

        # Use psycopg2 connection string with Kerberos
        conn_str = f"postgresql+psycopg2://{username}@{target['host']}:{target['port']}/postgres?gssencmode=require"
    else:
        user = target.get('user')
        password = target.get('password')
        if not user:
            print("ERROR: username not configured for password authentication")
            sys.exit(1)

        if password:
            conn_str = f"postgresql://{user}:{password}@{target['host']}:{target['port']}/postgres"
        else:
            conn_str = f"postgresql://{user}@{target['host']}:{target['port']}/postgres"

    try:
        # Try to create database using SQLAlchemy
        # Note: This connects to 'postgres' database first, then creates bronze_warehouse
        from sqlalchemy import create_engine
        from sqlalchemy.exc import ProgrammingError

        # Connect to default 'postgres' database
        engine = create_engine(conn_str, isolation_level="AUTOCOMMIT")

        print(f"\nCreating database: {target['database']}")

        try:
            with engine.connect() as conn:
                conn.execute(text(f"CREATE DATABASE {target['database']}"))
            print(f"✓ Database '{target['database']}' created successfully")
        except ProgrammingError as e:
            if "already exists" in str(e):
                print(f"✓ Database '{target['database']}' already exists")
            else:
                raise

        engine.dispose()

    except Exception as e:
        print(f"\nERROR creating database: {e}")
        print("\nTroubleshooting:")
        print("  1. Ensure PostgreSQL server allows connections from this host")
        print("  2. For Kerberos: Check that pg_hba.conf has 'hostgssenc' entries")
        print("  3. For password auth: Check that pg_hba.conf allows your user")
        print("\nYou can manually create the database:")
        print(f"  psql -h {target['host']} -c 'CREATE DATABASE {target['database']}'")
        print("\nThen re-run this script to create tables.")
        sys.exit(1)


def create_schema_and_tables(config):
    """Create bronze schema and tables"""
    target = config['target']

    print("\n" + "=" * 80)
    print("Step 2: Creating bronze schema and tables")
    print("=" * 80)

    # Build connection string for bronze_warehouse database
    if target.get('use_kerberos', True):
        username = get_kerberos_username()
        conn_str = f"postgresql+psycopg2://{username}@{target['host']}:{target['port']}/{target['database']}?gssencmode=require"
    else:
        user = target.get('user')
        password = target.get('password')
        if password:
            conn_str = f"postgresql://{user}:{password}@{target['host']}:{target['port']}/{target['database']}"
        else:
            conn_str = f"postgresql://{user}@{target['host']}:{target['port']}/{target['database']}"

    try:
        engine = create_engine(conn_str, echo=True)

        with engine.connect() as conn:
            # Create bronze schema
            print(f"\nCreating schema: {target['schema']}")
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {target['schema']}"))
            conn.commit()
            print(f"✓ Schema '{target['schema']}' created")

        # Create all Bronze tables
        print("\nCreating Bronze tables...")
        SQLModel.metadata.create_all(engine)
        print("✓ All Bronze tables created successfully")

        # List created tables
        with engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = '{target['schema']}'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]

            print("\nCreated tables in bronze schema:")
            for table in tables:
                print(f"  - {table}")

        engine.dispose()

    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


def verify_setup(config):
    """Verify the setup is complete"""
    target = config['target']

    print("\n" + "=" * 80)
    print("Step 3: Verifying setup")
    print("=" * 80)

    if target.get('use_kerberos', True):
        username = get_kerberos_username()
        conn_str = f"postgresql+psycopg2://{username}@{target['host']}:{target['port']}/{target['database']}?gssencmode=require"
    else:
        user = target.get('user')
        password = target.get('password')
        if password:
            conn_str = f"postgresql://{user}:{password}@{target['host']}:{target['port']}/{target['database']}"
        else:
            conn_str = f"postgresql://{user}@{target['host']}:{target['port']}/{target['database']}"

    try:
        engine = create_engine(conn_str)
        with engine.connect() as conn:
            # Check database exists
            result = conn.execute(text("SELECT current_database()"))
            db_name = result.scalar()
            print(f"✓ Connected to database: {db_name}")

            # Check schema exists
            result = conn.execute(text(f"""
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name = '{target['schema']}'
            """))
            if result.scalar():
                print(f"✓ Schema '{target['schema']}' exists")

            # Count tables
            result = conn.execute(text(f"""
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = '{target['schema']}'
            """))
            table_count = result.scalar()
            print(f"✓ Found {table_count} table(s) in bronze schema")

        engine.dispose()

        print("\n" + "=" * 80)
        print("SUCCESS! Bronze warehouse is ready to use.")
        print("=" * 80)
        print("\nNext steps:")
        print("  1. Run: python test_loader.py")
        print("  2. Check the data in bronze_warehouse")

    except Exception as e:
        print(f"ERROR during verification: {e}")
        sys.exit(1)


def main():
    print("=" * 80)
    print("Bronze Warehouse Setup")
    print("=" * 80)

    # Load configuration
    config = load_config()
    print(f"\nSource: {config['source']['database']} on {config['source']['host']}")
    print(f"Target: {config['target']['database']} on {config['target']['host']}")

    # Create database
    create_database(config)

    # Create schema and tables
    create_schema_and_tables(config)

    # Verify setup
    verify_setup(config)


if __name__ == "__main__":
    main()
