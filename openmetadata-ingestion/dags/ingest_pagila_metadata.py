"""
OpenMetadata Ingestion DAG - Pagila PostgreSQL
===============================================

Programmatically ingests pagila database schema into OpenMetadata.
This demonstrates the "everything as code" approach to metadata cataloging.

Architecture:
    Source: pagila-postgres:5432/pagila (PostgreSQL)
        ↓
    Extract: Schema metadata (tables, columns, relationships)
        ↓
    Send: OpenMetadata API (http://openmetadata-server:8585/api)
        ↓
    Store: Platform PostgreSQL (openmetadata_db)
        ↓
    Browse: OpenMetadata UI (http://localhost:8585)

What This DAG Does:
- Connects to pagila PostgreSQL database
- Extracts table and column metadata
- Discovers foreign key relationships
- Sends metadata to OpenMetadata API
- Makes data discoverable in OpenMetadata UI

Run This First!
This is the simplest ingestion example with no authentication complexity.
Use it to understand the basic pattern before trying SQL Server with Kerberos.

Schedule:
- Default: Manual trigger (schedule_interval=None)
- Recommended: '@weekly' to keep catalog fresh

Tags: openmetadata, ingestion, pagila, postgres
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from metadata.ingestion.api.workflow import Workflow


def ingest_pagila_metadata(**context):
    """
    Ingest pagila PostgreSQL schema metadata into OpenMetadata.

    This function:
    1. Connects to pagila PostgreSQL database
    2. Extracts schema metadata (tables, columns, types)
    3. Discovers relationships (foreign keys)
    4. Sends metadata to OpenMetadata API

    No return value - raises exception on failure.
    """

    # Configuration as code (version controlled!)
    config = {
        "source": {
            # Source type: PostgreSQL
            "type": "postgres",

            # Service name (appears in OpenMetadata UI)
            "serviceName": "pagila-local",

            # Connection configuration
            "serviceConnection": {
                "config": {
                    "type": "Postgres",
                    # Host:port (use Docker network hostname)
                    "hostPort": "pagila-postgres:5432",
                    # Credentials
                    "username": "postgres",
                    "password": "postgres",  # TODO: Use Airflow variable in production
                    # Database to catalog
                    "database": "pagila"
                }
            },

            # What to ingest
            "sourceConfig": {
                "config": {
                    "type": "DatabaseMetadata",

                    # Schema filters (regex patterns)
                    "schemaFilterPattern": {
                        "includes": ["public"]  # Only public schema
                    },

                    # Table filters (regex patterns)
                    "tableFilterPattern": {
                        "includes": [".*"]  # All tables (. = any char, * = zero or more)
                    },

                    # Include/exclude patterns for views, stored procedures, etc.
                    # "includeViews": True,
                    # "includeTables": True,
                }
            }
        },

        # Destination: OpenMetadata API
        "sink": {
            "type": "metadata-rest",
            "config": {
                "openMetadataServerConfig": {
                    # OpenMetadata server endpoint (Docker network hostname)
                    "hostPort": "http://openmetadata-server:8585/api"
                    # Note: No auth token needed for local development (basic auth)
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

    # Create and execute ingestion workflow
    print("OpenMetadata Ingestion Workflow")
    print("================================")
    print(f"Source: PostgreSQL (pagila-postgres:5432/pagila)")
    print(f"Target: OpenMetadata (http://openmetadata-server:8585/api)")
    print("")

    workflow = Workflow.create(config)
    workflow.execute()
    workflow.raise_from_status()
    workflow.stop()

    print("")
    print("✓ Metadata ingestion completed successfully!")
    print("")
    print("View results:")
    print("  OpenMetadata UI: http://localhost:8585")
    print("  Search for: film, actor, customer, etc.")


# DAG definition
with DAG(
    dag_id='openmetadata_ingest_pagila',

    # Description (appears in Airflow UI)
    description='Ingest pagila PostgreSQL schema into OpenMetadata catalog',

    # Documentation
    doc_md=__doc__,

    # Schedule
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,  # Manual trigger (change to '@weekly' for automation)
    catchup=False,

    # Tags (for filtering in Airflow UI)
    tags=['openmetadata', 'ingestion', 'pagila', 'postgres'],

    # DAG-level settings
    max_active_runs=1,  # Only one ingestion at a time

) as dag:

    # Single task: Run ingestion
    ingest_task = PythonOperator(
        task_id='ingest_pagila_schema',
        python_callable=ingest_pagila_metadata,

        # Task documentation
        doc_md="""
        ## Pagila Metadata Ingestion

        Extracts schema metadata from pagila PostgreSQL database and
        sends it to OpenMetadata for cataloging.

        ### What Gets Ingested
        - Database: pagila
        - Schema: public
        - Tables: All tables (actor, film, customer, etc.)
        - Columns: Names, types, nullability
        - Relationships: Foreign keys

        ### Configuration
        See `ingest_pagila_metadata()` function for full config.

        ### Expected Runtime
        ~10 seconds

        ### Troubleshooting
        If this fails, check:
        1. Is pagila database running? `docker ps | grep pagila`
        2. Is OpenMetadata running? `make platform-status`
        3. Network connectivity? All services on platform_network
        """,
    )

# DAG structure (simple - just one task)
# ingest_task
