#!/usr/bin/env python3
"""
===============================================================================
FILL-IN-THE-BLANKS SQL SERVER BRONZE INGESTION
===============================================================================

This is a working example that you can run IMMEDIATELY with mock data,
then modify for your real SQL Server.

HOW TO USE:
-----------
1. Run AS-IS first to see it work with mock data
2. Then fill in YOUR values in the clearly marked sections
3. Run again with your real data

NO NEED TO CREATE NEW FILES - Just edit this one!
===============================================================================
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# ==============================================================================
# SECTION 1: CHOOSE YOUR MODE
# ==============================================================================

# Set this to False when ready to use your real SQL Server
USE_MOCK_DATA = True  # <- CHANGE TO False WHEN READY FOR REAL DATA

# ==============================================================================
# SECTION 2: MOCK DATA CONFIGURATION (WORKS OUT OF THE BOX!)
# ==============================================================================

if USE_MOCK_DATA:
    print("🎭 RUNNING IN MOCK MODE - Using test data")
    print("   Change USE_MOCK_DATA to False when ready for real data\n")

    # This configuration works with the included docker-compose.kdc-test.yml
    SQL_CONFIG = {
        "server": "localhost",           # Local test SQL Server
        "port": 1433,
        "database": "TestWarehouse",     # Mock database
        "source_schema": "dbo",
        "source_table": "Customer",      # Mock table with 10 rows
        "auth_type": "sql",              # Using SQL auth for mock
        "username": "sa",                # Test username
        "password": "YourStrong@Password123",  # Test password
        "trust_cert": True,              # Self-signed cert
    }

    BRONZE_CONFIG = {
        "target_schema": "bronze",
        "target_table": "mock_customer_bronze",
    }

# ==============================================================================
# SECTION 3: YOUR REAL CONFIGURATION (FILL IN THE BLANKS!)
# ==============================================================================

else:
    print("🏢 RUNNING IN PRODUCTION MODE - Using real SQL Server")
    print("   Make sure you have a valid Kerberos ticket!\n")

    # FILL IN YOUR ACTUAL VALUES BELOW:
    # ----------------------------------

    SQL_CONFIG = {
        # YOUR SQL SERVER CONNECTION:
        "server": "_______________",     # <- FILL IN: Your SQL Server (e.g., "sql.company.com")
        "port": 1433,                    # <- Usually 1433, change if different
        "database": "_______________",   # <- FILL IN: Your database (e.g., "DataWarehouse")

        # YOUR TABLE TO INGEST:
        "source_schema": "dbo",          # <- FILL IN: Schema (usually "dbo")
        "source_table": "_______________", # <- FILL IN: Your table (e.g., "Customer")

        # AUTHENTICATION (keep as kerberos for NT Auth):
        "auth_type": "kerberos",         # <- Keep this for Windows Auth

        # OR use SQL auth (uncomment and fill in):
        # "auth_type": "sql",
        # "username": "_______________",  # <- FILL IN: SQL username
        # "password": "_______________",  # <- FILL IN: SQL password

        # CERTIFICATES:
        "trust_cert": True,              # <- Set False if using proper certs
    }

    BRONZE_CONFIG = {
        # WHERE TO SAVE IN BRONZE:
        "target_schema": "bronze",                    # <- Usually keep as "bronze"
        "target_table": "_______________",           # <- FILL IN: Name in Bronze (e.g., "customer_daily")
    }

    # VALIDATION: Check if blanks were filled
    blanks = [k for k, v in SQL_CONFIG.items() if v == "_______________"]
    if blanks:
        print("❌ ERROR: Please fill in the blanks for:", blanks)
        print("\nEdit this file and replace _______________  with your actual values")
        sys.exit(1)

# ==============================================================================
# SECTION 4: THE ACTUAL INGESTION (NO NEED TO MODIFY!)
# ==============================================================================

def setup_mock_environment():
    """Set up mock environment for testing."""
    print("📦 Setting up mock environment...")

    # For mock mode, we'll use a local SQL Server container
    # Make sure docker-compose.kdc-test.yml is running!

    print("   ✅ Mock configuration loaded")
    print(f"   📍 Server: {SQL_CONFIG['server']}:{SQL_CONFIG['port']}")
    print(f"   📊 Table: {SQL_CONFIG['source_schema']}.{SQL_CONFIG['source_table']}")
    print()

def check_prerequisites():
    """Check that everything is set up correctly."""
    print("🔍 Checking prerequisites...")

    if USE_MOCK_DATA:
        # For mock data, just check Python packages
        try:
            import pyodbc
            print("   ✅ pyodbc installed")
        except ImportError:
            print("   ❌ pyodbc not installed - run: pip install pyodbc")
            return False

    else:
        # For real data, check Kerberos
        if SQL_CONFIG["auth_type"] == "kerberos":
            krb5ccname = os.environ.get('KRB5CCNAME', '/tmp/krb5cc_' + str(os.getuid()))
            if os.path.exists(krb5ccname):
                print(f"   ✅ Kerberos ticket found: {krb5ccname}")
            else:
                print(f"   ❌ No Kerberos ticket at {krb5ccname}")
                print("      Run: kinit YOUR_USERNAME@COMPANY.COM")
                return False

    return True

def run_ingestion():
    """Run the actual Bronze ingestion."""
    try:
        # Import the datakit
        from datakit_sqlserver_bronze import (
            SQLServerConfig,
            SQLServerKerberosConnector,
            BronzeIngestionPipeline
        )
    except ImportError:
        print("❌ Datakit not installed!")
        print("   Run: pip install -e ../datakit_sqlserver_bronze_kerberos")
        sys.exit(1)

    print("\n" + "="*60)
    print("STARTING BRONZE INGESTION")
    print("="*60)

    # Create configuration
    config = SQLServerConfig(
        server=SQL_CONFIG["server"],
        port=SQL_CONFIG["port"],
        database=SQL_CONFIG["database"],
        auth_type=SQL_CONFIG["auth_type"],
        username=SQL_CONFIG.get("username"),
        password=SQL_CONFIG.get("password"),
        trust_server_certificate=SQL_CONFIG.get("trust_cert", True),
        application_name="FillInTheBlanksExample"
    )

    # Test connection
    print("\n🔌 Testing connection...")
    connector = SQLServerKerberosConnector(config)
    success, message = connector.test_connection()

    if not success:
        print(f"❌ Connection failed: {message}")
        if USE_MOCK_DATA:
            print("\n💡 Make sure the test SQL Server is running:")
            print("   cd ../../kerberos-astronomer")
            print("   docker-compose -f docker-compose.kdc-test.yml up -d")
        sys.exit(1)

    print(f"✅ Connected successfully!")

    # Get table info
    print(f"\n📊 Checking table {SQL_CONFIG['source_schema']}.{SQL_CONFIG['source_table']}...")

    try:
        metadata = connector.get_table_metadata(
            SQL_CONFIG["source_table"],
            SQL_CONFIG["source_schema"]
        )
        print(f"   Found {metadata['row_count']:,} rows")
        print(f"   Found {len(metadata['columns'])} columns")

        # Show columns
        print("\n   Columns:")
        for col in metadata['columns'][:5]:
            print(f"      - {col['name']} ({col['type']})")
        if len(metadata['columns']) > 5:
            print(f"      ... and {len(metadata['columns'])-5} more")

    except Exception as e:
        print(f"❌ Could not access table: {e}")
        sys.exit(1)

    # Run ingestion
    print(f"\n🚀 Starting ingestion to {BRONZE_CONFIG['target_schema']}.{BRONZE_CONFIG['target_table']}...")

    pipeline = BronzeIngestionPipeline(config)
    start_time = datetime.now()

    try:
        rows_ingested = pipeline.ingest_table(
            source_table=SQL_CONFIG["source_table"],
            source_schema=SQL_CONFIG["source_schema"],
            target_table=BRONZE_CONFIG["target_table"],
            target_schema=BRONZE_CONFIG["target_schema"],
            batch_size=1000
        )

        duration = (datetime.now() - start_time).total_seconds()

        print("\n" + "="*60)
        print("✅ INGESTION COMPLETE!")
        print("="*60)
        print(f"   Rows ingested: {rows_ingested:,}")
        print(f"   Duration: {duration:.2f} seconds")
        print(f"   Target: {BRONZE_CONFIG['target_schema']}.{BRONZE_CONFIG['target_table']}")

        if USE_MOCK_DATA:
            print("\n🎉 Mock ingestion successful!")
            print("   Now change USE_MOCK_DATA to False and fill in your real values")
        else:
            print("\n🎉 Production ingestion successful!")
            print("   Your data is now in the Bronze layer")

    except Exception as e:
        print(f"\n❌ Ingestion failed: {e}")
        sys.exit(1)

def main():
    """Main entry point."""
    print("="*60)
    print("FILL-IN-THE-BLANKS BRONZE INGESTION")
    print("="*60)

    if USE_MOCK_DATA:
        setup_mock_environment()

    if not check_prerequisites():
        print("\n⚠️  Please fix the issues above and try again")
        sys.exit(1)

    run_ingestion()

    print("\n" + "="*60)
    print("NEXT STEPS:")
    print("="*60)

    if USE_MOCK_DATA:
        print("1. You've successfully run the mock ingestion!")
        print("2. Now edit this file and set USE_MOCK_DATA = False")
        print("3. Fill in your actual SQL Server details")
        print("4. Run again to ingest your real data")
    else:
        print("1. Check your Bronze layer for the ingested data")
        print("2. Schedule this script to run regularly")
        print("3. Add more tables by copying this script")
        print("4. Monitor ingestion with logging/alerts")

# ==============================================================================
# RUN THE SCRIPT
# ==============================================================================

if __name__ == "__main__":
    main()

# ==============================================================================
# QUICK REFERENCE
# ==============================================================================
"""
TROUBLESHOOTING:
---------------
- "No module named datakit_sqlserver_bronze":
  → Install: pip install -e ../datakit_sqlserver_bronze_kerberos

- "Connection failed" (mock mode):
  → Start test SQL: docker-compose -f docker-compose.kdc-test.yml up -d

- "No Kerberos ticket" (production):
  → Get ticket: kinit YOUR_USERNAME@COMPANY.COM

- "Table not found":
  → Check table name and schema
  → Verify you have SELECT permissions

CUSTOMIZATION:
-------------
- Change batch size: Edit batch_size=1000 in pipeline.ingest_table()
- Add more tables: Copy this file and change source_table
- Different schedule: Use with Airflow DAG
- Email alerts: Add try/except with email notification
"""