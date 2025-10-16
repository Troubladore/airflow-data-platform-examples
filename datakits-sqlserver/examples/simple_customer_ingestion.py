#!/usr/bin/env python3
"""
SIMPLE SQL SERVER BRONZE INGESTION EXAMPLE
==========================================

This example shows how to ingest ONE table from SQL Server using NT Authentication.

WHAT THIS DOES:
- Connects to your SQL Server using Windows Authentication (Kerberos)
- Reads the Customer table
- Adds Bronze metadata (when it was loaded, where it came from)
- Saves to Bronze layer

BEFORE RUNNING:
1. Update the CONFIGURATION section below with your SQL Server details
2. Ensure you have a valid Kerberos ticket (run: klist)
3. Install the datakit: pip install -e ../datakit_sqlserver_bronze_kerberos

TO RUN:
python simple_customer_ingestion.py
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path so we can import the datakit
sys.path.insert(0, str(Path(__file__).parent.parent))

from datakit_sqlserver_bronze_kerberos.src.datakit_sqlserver_bronze import (
    SQLServerConfig,
    SQLServerKerberosConnector,
    BronzeIngestionPipeline
)

# ==============================================================================
# CONFIGURATION - UPDATE THESE VALUES FOR YOUR ENVIRONMENT
# ==============================================================================

# Step 1: SQL Server Connection Details
SQL_SERVER_HOST = "sql.company.com"      # <- CHANGE THIS to your SQL Server hostname
SQL_SERVER_PORT = 1433                   # <- Usually 1433, change if different
SQL_SERVER_DATABASE = "AdventureWorks"   # <- CHANGE THIS to your database name

# Step 2: Table to Ingest
SOURCE_SCHEMA = "dbo"                    # <- Schema containing your table
SOURCE_TABLE = "Customer"                # <- CHANGE THIS to your table name

# Step 3: Where to Save in Bronze Layer
BRONZE_SCHEMA = "bronze"                 # <- Target schema in Bronze
BRONZE_TABLE = "customer_snapshot"       # <- What to call it in Bronze

# Step 4: Authentication Method
# For Kerberos/NT Auth, you don't need username/password
# Just make sure you have a valid ticket (run: klist)
AUTH_TYPE = "kerberos"                   # <- Use "sql" if using username/password

# Optional: For SQL Authentication (instead of Kerberos)
# Uncomment these lines and set AUTH_TYPE = "sql" above
# SQL_USERNAME = "your_username"
# SQL_PASSWORD = "your_password"

# ==============================================================================
# KERBEROS SETUP CHECK
# ==============================================================================

def check_kerberos_setup():
    """Verify Kerberos is configured correctly."""
    print("🔍 Checking Kerberos setup...")

    # Check if ticket cache exists
    krb5ccname = os.environ.get('KRB5CCNAME', '/tmp/krb5cc_' + str(os.getuid()))

    if os.path.exists(krb5ccname):
        print(f"✅ Kerberos ticket cache found: {krb5ccname}")
    else:
        print(f"⚠️  No ticket cache at {krb5ccname}")
        print("   Run: kinit YOUR_USERNAME@COMPANY.COM")
        return False

    # Check if krb5.conf exists
    krb5_config = os.environ.get('KRB5_CONFIG', '/etc/krb5.conf')

    if os.path.exists(krb5_config):
        print(f"✅ Kerberos config found: {krb5_config}")
    else:
        print(f"❌ No krb5.conf at {krb5_config}")
        print("   This file should be configured by your IT team")
        return False

    print("✅ Kerberos appears to be configured")
    return True

# ==============================================================================
# MAIN INGESTION LOGIC
# ==============================================================================

def main():
    """Run the Bronze ingestion for a single table."""

    print("=" * 60)
    print("SQL SERVER BRONZE INGESTION - SIMPLE EXAMPLE")
    print("=" * 60)
    print()

    # Step 1: Check Kerberos (only if using Kerberos auth)
    if AUTH_TYPE == "kerberos":
        if not check_kerberos_setup():
            print("\n❌ Please fix Kerberos setup first")
            sys.exit(1)

    print()
    print("📋 Configuration:")
    print(f"   Server: {SQL_SERVER_HOST}:{SQL_SERVER_PORT}")
    print(f"   Database: {SQL_SERVER_DATABASE}")
    print(f"   Source: {SOURCE_SCHEMA}.{SOURCE_TABLE}")
    print(f"   Target: {BRONZE_SCHEMA}.{BRONZE_TABLE}")
    print(f"   Auth Type: {AUTH_TYPE}")
    print()

    # Step 2: Create configuration
    config = SQLServerConfig(
        server=SQL_SERVER_HOST,
        port=SQL_SERVER_PORT,
        database=SQL_SERVER_DATABASE,
        auth_type=AUTH_TYPE,

        # For SQL auth (uncomment if needed):
        # username=SQL_USERNAME,
        # password=SQL_PASSWORD,

        # Optional settings:
        trust_server_certificate=True,  # Set to True if using self-signed certs
        application_name="BronzeIngestionExample"
    )

    # Step 3: Test connection
    print("🔌 Testing connection to SQL Server...")
    connector = SQLServerKerberosConnector(config)
    success, message = connector.test_connection()

    if not success:
        print(f"❌ Connection failed: {message}")
        sys.exit(1)

    print(f"✅ {message}")
    print()

    # Step 4: Get table information
    print(f"📊 Getting information about {SOURCE_SCHEMA}.{SOURCE_TABLE}...")

    try:
        metadata = connector.get_table_metadata(SOURCE_TABLE, SOURCE_SCHEMA)
        print(f"   Columns: {len(metadata['columns'])}")
        print(f"   Rows: {metadata['row_count']:,}")

        # Show first few columns
        print("   Sample columns:")
        for col in metadata['columns'][:5]:
            print(f"      - {col['name']} ({col['type']})")
        if len(metadata['columns']) > 5:
            print(f"      ... and {len(metadata['columns']) - 5} more columns")

    except Exception as e:
        print(f"❌ Could not get table metadata: {e}")
        print("   Make sure the table exists and you have permissions")
        sys.exit(1)

    print()

    # Step 5: Run the ingestion
    print(f"🚀 Starting ingestion of {SOURCE_SCHEMA}.{SOURCE_TABLE}...")
    print(f"   This will:")
    print(f"   1. Read all data from {SOURCE_TABLE}")
    print(f"   2. Add Bronze metadata columns (_bronze_loaded_at, etc.)")
    print(f"   3. Save to {BRONZE_SCHEMA}.{BRONZE_TABLE}")
    print()

    # Create pipeline
    pipeline = BronzeIngestionPipeline(config)

    try:
        # Ingest the table
        start_time = datetime.now()

        rows_ingested = pipeline.ingest_table(
            source_table=SOURCE_TABLE,
            source_schema=SOURCE_SCHEMA,
            target_table=BRONZE_TABLE,
            target_schema=BRONZE_SCHEMA,
            batch_size=10000  # Process 10,000 rows at a time
        )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        print()
        print("✅ INGESTION COMPLETE!")
        print(f"   Rows ingested: {rows_ingested:,}")
        print(f"   Duration: {duration:.2f} seconds")
        print(f"   Rate: {rows_ingested/duration:.0f} rows/second")
        print()
        print(f"📦 Data saved to: {BRONZE_SCHEMA}.{BRONZE_TABLE}")

        # Show what Bronze metadata was added
        print()
        print("📝 Bronze metadata columns added:")
        print("   - _bronze_loaded_at: When the data was loaded")
        print("   - _bronze_source_system: 'sqlserver'")
        print(f"   - _bronze_source_schema: '{SOURCE_SCHEMA}'")
        print(f"   - _bronze_source_table: '{SOURCE_TABLE}'")

    except Exception as e:
        print()
        print(f"❌ Ingestion failed: {e}")
        print()
        print("Common issues:")
        print("  - Table doesn't exist")
        print("  - No read permissions")
        print("  - Kerberos ticket expired (run: kinit)")
        print("  - Network/firewall issues")
        sys.exit(1)

    print()
    print("=" * 60)
    print("SUCCESS! Your data is now in the Bronze layer.")
    print("=" * 60)

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def show_sample_data():
    """Optional: Show a sample of the ingested data."""
    print("\n📋 Sample of ingested data:")

    # This would connect to your Bronze layer and show sample rows
    # Implementation depends on where your Bronze layer is stored
    pass

if __name__ == "__main__":
    main()

    # Uncomment to show sample data after ingestion
    # show_sample_data()