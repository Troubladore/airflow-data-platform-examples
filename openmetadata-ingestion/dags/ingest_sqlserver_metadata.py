"""
OpenMetadata Ingestion DAG - SQL Server with Kerberos
======================================================

Programmatically ingests SQL Server schema using Kerberos authentication.
This demonstrates enterprise-grade security with the platform Kerberos sidecar.

Architecture:
    Host Kerberos Ticket
        ↓ (via sidecar)
    Astronomer Container (this DAG)
        ↓ (Kerberos auth - no password!)
    SQL Server (sqlserver01.company.com)
        ↓ (extract metadata)
    OpenMetadata API
        ↓ (store)
    OpenMetadata UI (browse)

What This DAG Does:
- Uses Kerberos ticket from platform sidecar (no username/password!)
- Connects to corporate SQL Server with integrated authentication
- Extracts table and column metadata
- Discovers foreign key relationships
- Sends metadata to OpenMetadata API
- Makes corporate data discoverable

Security Benefits:
- ✅ No credentials in code
- ✅ Uses existing Kerberos ticket
- ✅ Leverages platform sidecar pattern
- ✅ Approved by security team

Prerequisites:
- Platform services running (make platform-start)
- Valid Kerberos ticket (kinit your.name@DOMAIN.COM)
- SQL Server accessible and tested (test-sql-direct.sh)

Schedule:
- Default: Manual trigger
- Recommended: '@weekly' (schema changes less frequently than daily data)

Tags: openmetadata, ingestion, sqlserver, kerberos
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from metadata.ingestion.api.workflow import Workflow
import os


def ingest_sqlserver_metadata(**context):
    """
    Ingest SQL Server schema metadata using Kerberos authentication.

    This function:
    1. Verifies Kerberos ticket is available
    2. Connects to SQL Server using integrated auth (no password!)
    3. Extracts schema metadata
    4. Sends to OpenMetadata API

    Environment variables required:
    - KRB5CCNAME: Path to Kerberos ticket cache
    - KRB5_CONFIG: Path to krb5.conf

    No return value - raises exception on failure.
    """

    # Verify Kerberos configuration
    krb5ccname = os.environ.get('KRB5CCNAME')
    if not krb5ccname:
        raise ValueError("KRB5CCNAME not set! Check docker-compose.override.yml")

    print("Kerberos Configuration:")
    print(f"  KRB5CCNAME: {krb5ccname}")
    print(f"  KRB5_CONFIG: {os.environ.get('KRB5_CONFIG', '/etc/krb5.conf')}")
    print("")

    # Configuration as code
    # NOTE: Customize these values for your SQL Server!
    config = {
        "source": {
            # Source type: Microsoft SQL Server
            "type": "mssql",

            # Service name (appears in OpenMetadata UI)
            "serviceName": "corporate-sql-server",

            # Connection configuration
            "serviceConnection": {
                "config": {
                    "type": "Mssql",

                    # Connection scheme (pyodbc for Kerberos support)
                    "scheme": "mssql+pyodbc",

                    # SQL Server hostname and port
                    # MUST be FQDN (not IP or short name) for Kerberos!
                    "hostPort": "sqlserver01.company.com:1433",

                    # Database to catalog
                    # TODO: Customize for your database
                    "database": "TestDB",

                    # Kerberos authentication (NO username/password!)
                    "connectionOptions": {
                        # ODBC Driver
                        "driver": "ODBC Driver 18 for SQL Server",

                        # Kerberos settings
                        "TrustedConnection": "yes",  # Use Kerberos ticket!
                        "Trusted_Connection": "yes",  # Alternative syntax
                        "Encrypt": "yes",
                        "TrustServerCertificate": "yes",  # Accept self-signed certs

                        # Connection behavior
                        "timeout": "30",
                        "Connect Timeout": "30"
                    }
                }
            },

            # What to ingest
            "sourceConfig": {
                "config": {
                    "type": "DatabaseMetadata",

                    # Schema filters
                    "schemaFilterPattern": {
                        "includes": ["dbo"]  # Default schema (customize as needed)
                    },

                    # Table filters
                    "tableFilterPattern": {
                        "includes": [".*"]  # All tables
                        # Exclude system tables if needed:
                        # "excludes": ["sys.*", "INFORMATION_SCHEMA.*"]
                    },

                    # Include views and stored procedures
                    "includeViews": True,
                    "includeTables": True,
                }
            }
        },

        # Destination: OpenMetadata API
        "sink": {
            "type": "metadata-rest",
            "config": {
                "openMetadataServerConfig": {
                    "hostPort": "http://openmetadata-server:8585/api"
                }
            }
        },

        # Workflow configuration
        "workflowConfig": {
            "openMetadataServerConfig": {
                "hostPort": "http://openmetadata-server:8585/api"
            }
        }
    }

    # Execute ingestion workflow
    print("OpenMetadata Ingestion Workflow")
    print("================================")
    print(f"Source: SQL Server (sqlserver01.company.com:1433)")
    print(f"Database: TestDB")
    print(f"Authentication: Kerberos (Integrated Windows Auth)")
    print(f"Target: OpenMetadata (http://openmetadata-server:8585/api)")
    print("")

    # Verify Kerberos ticket before attempting connection
    print("Checking Kerberos ticket...")
    import subprocess
    try:
        result = subprocess.run(['klist', '-s'], check=True, capture_output=True)
        print("  ✓ Valid Kerberos ticket found")

        # Show ticket details
        ticket_info = subprocess.run(['klist'], capture_output=True, text=True)
        print("")
        print("Ticket details:")
        for line in ticket_info.stdout.split('\n')[:5]:
            print(f"  {line}")
    except subprocess.CalledProcessError:
        raise RuntimeError(
            "No valid Kerberos ticket found!\n"
            "Run: kinit your.name@DOMAIN.COM\n"
            "Then check: docker exec <container> klist"
        )

    print("")
    print("Connecting to SQL Server with Kerberos...")

    # Create and execute workflow
    workflow = Workflow.create(config)
    workflow.execute()
    workflow.raise_from_status()
    workflow.stop()

    print("")
    print("✓ SQL Server metadata ingestion completed successfully!")
    print("")
    print("View results:")
    print("  OpenMetadata UI: http://localhost:8585")
    print("  Service: corporate-sql-server")
    print("  Database: TestDB")
    print("")
    print("Security note:")
    print("  ✓ No password in code (used Kerberos ticket)")
    print("  ✓ Ticket from platform sidecar (/krb5/cache/krb5cc)")


# DAG definition
with DAG(
    dag_id='openmetadata_ingest_sqlserver',

    # Description
    description='Ingest SQL Server schema using Kerberos authentication',

    # Documentation
    doc_md=__doc__,

    # Schedule
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,  # Manual trigger (change to '@weekly' for automation)
    catchup=False,

    # Tags
    tags=['openmetadata', 'ingestion', 'sqlserver', 'kerberos'],

    # DAG-level settings
    max_active_runs=1,

) as dag:

    # Single task: Run ingestion with Kerberos
    ingest_task = PythonOperator(
        task_id='ingest_sqlserver_schema',
        python_callable=ingest_sqlserver_metadata,

        # Task documentation
        doc_md="""
        ## SQL Server Metadata Ingestion (Kerberos)

        Extracts schema metadata from corporate SQL Server database
        using Kerberos authentication (no password required!).

        ### What Gets Ingested
        - Database: TestDB (customize in DAG code)
        - Schema: dbo (customize as needed)
        - Tables: All tables
        - Columns: Names, types, nullability
        - Relationships: Foreign keys
        - Views: Included

        ### Kerberos Authentication
        This DAG uses the Kerberos ticket from the platform sidecar.
        No username or password in the code!

        Connection flow:
        1. Container has KRB5CCNAME=/krb5/cache/krb5cc
        2. pyodbc uses TrustedConnection=yes
        3. SQL Server validates Kerberos ticket
        4. Connection succeeds

        ### Expected Runtime
        ~10-30 seconds depending on database size

        ### Troubleshooting
        If this fails:
        1. Check Kerberos ticket: `docker exec <container> klist -s`
        2. Test direct SQL: `cd platform-bootstrap && ./diagnostics/test-sql-direct.sh sqlserver01.company.com TestDB`
        3. Check logs for specific error
        4. Verify SQL Server SPN configuration (ask DBA)

        ### Customization
        To catalog a different SQL Server database:
        1. Copy this file to `ingest_<database>_metadata.py`
        2. Change `hostPort`, `database`, `serviceName`
        3. Adjust schema/table filters if needed
        4. Commit and run!
        """,
    )

# DAG structure (simple - just one task)
# ingest_task
