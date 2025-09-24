"""
SQL Server Bronze Ingestion DAG - Environment-Aware
====================================================

This DAG demonstrates:
1. Bronze ingestion from SQL Server with Kerberos
2. Automatic adaptation between Docker (local) and Kubernetes (int/qa/prod)
3. How to integrate into your company's environment

WHAT THIS DOES:
- Ingests Customer and Order tables from SQL Server
- Works identically on developer workstation (Docker) and production (K8s)
- Uses the same datakit images across all environments

WHERE TO MODIFY:
- Lines 40-41: Your SQL Server tables
- Line 95-96: Your warehouse configuration
- Line 120+: Add more tables as needed
"""

from datetime import datetime, timedelta
from typing import Dict, Any
import os
import sys

from airflow import DAG
from airflow.decorators import task

# Add deployment directory to path for environment abstraction
sys.path.append('/usr/local/airflow/deployment')
from environment_abstraction import DatakitOperator, get_environment

# ==============================================================================
# CONFIGURATION - Modify for your company
# ==============================================================================

# Tables to ingest (add yours here)
TABLES_TO_INGEST = [
    "dbo.Customer",      # <- CHANGE: Your first table
    "dbo.Orders",        # <- CHANGE: Your second table
    # "dbo.YourTable",   # <- ADD: More tables as needed
]

# Datakit versions (managed by your CI/CD)
DATAKIT_VERSIONS = {
    'local': 'latest',      # Developers use latest
    'int': 'v1.2.3',        # Integration uses specific version
    'qa': 'v1.2.3',         # QA matches integration
    'prod': 'v1.2.2',       # Production on stable version
}

# ==============================================================================
# DAG DEFINITION
# ==============================================================================

default_args = {
    'owner': 'data-platform',
    'depends_on_past': False,
    'email': ['data-team@company.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'sqlserver_bronze_ingestion',
    default_args=default_args,
    description='Environment-aware Bronze ingestion from SQL Server',
    schedule_interval='@daily',
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['bronze', 'sql-server', 'kerberos', 'multi-env'],
) as dag:

    # Detect environment for this run
    current_env = get_environment()
    datakit_version = DATAKIT_VERSIONS.get(current_env, 'stable')

    @task
    def log_environment() -> Dict[str, Any]:
        """Log which environment we're running in."""
        import socket

        env_info = {
            'environment': current_env,
            'hostname': socket.gethostname(),
            'datakit_version': datakit_version,
            'executor': os.getenv('AIRFLOW__CORE__EXECUTOR', 'unknown'),
            'namespace': os.getenv('AIRFLOW_NAMESPACE', 'local'),
        }

        print("=" * 60)
        print(f"Running in {current_env.upper()} environment")
        print(f"Datakit version: {datakit_version}")
        print(f"Hostname: {env_info['hostname']}")
        print("=" * 60)

        # Different warehouse targets per environment
        warehouse_config = {
            'local': {
                'host': 'bronze-warehouse',
                'port': 5432,
                'database': 'bronze',
            },
            'int': {
                'host': 'bronze-warehouse.int.company.com',
                'port': 5432,
                'database': 'bronze_int',
            },
            'qa': {
                'host': 'bronze-warehouse.qa.company.com',
                'port': 5432,
                'database': 'bronze_qa',
            },
            'prod': {
                'host': 'bronze-warehouse.prod.company.com',
                'port': 5432,
                'database': 'bronze_prod',
            }
        }

        env_info['warehouse'] = warehouse_config.get(current_env)
        return env_info

    @task
    def verify_kerberos() -> bool:
        """Verify Kerberos ticket is available."""
        # This runs in the Airflow scheduler/worker, not the datakit
        krb5ccname = os.environ.get('KRB5CCNAME', '/krb5/cache/krb5cc')

        if current_env == 'local':
            # Local might use password auth for testing
            print(f"Local environment - checking ticket at {krb5ccname}")
            if not os.path.exists(krb5ccname):
                print("WARNING: No ticket cache, using password auth for local testing")
                return True  # Allow local testing without Kerberos
        else:
            # K8s environments must have valid ticket
            if not os.path.exists(krb5ccname):
                raise FileNotFoundError(
                    f"Kerberos ticket required in {current_env} environment"
                )

        return True

    # Get environment info
    env_info = log_environment()

    # Verify Kerberos
    krb_check = verify_kerberos()

    # Create Bronze ingestion tasks for each table
    ingestion_tasks = []

    for table in TABLES_TO_INGEST:
        # Clean table name for task ID
        task_id = f"ingest_{table.replace('.', '_').lower()}"

        # Create operator that works in any environment
        ingest_task = DatakitOperator.create(
            task_id=task_id,
            datakit_name='sqlserver-bronze',
            datakit_version=datakit_version,
            command=f'datakit-sqlserver ingest-table {table}',
            environment_vars={
                'MSSQL_SERVER': '{{ var.value.mssql_server }}',  # From Airflow Variables
                'MSSQL_DATABASE': '{{ var.value.mssql_database }}',
                'SOURCE_TABLE': table,
                'BRONZE_HOST': env_info['warehouse']['host'],
                'BRONZE_PORT': str(env_info['warehouse']['port']),
                'BRONZE_DATABASE': env_info['warehouse']['database'],
            },
            # These parameters differ between Docker and K8s
            # but DatakitOperator handles the differences
            pool='bronze_ingestion_pool',
            retries=2,
        )

        ingestion_tasks.append(ingest_task)

        # Set dependencies
        env_info >> krb_check >> ingest_task

    @task
    def record_ingestion_metadata(context) -> None:
        """Record metadata about the ingestion."""
        # This demonstrates how to track lineage across environments
        from airflow.models import Variable
        import json

        metadata = {
            'dag_run_id': context['dag_run'].run_id,
            'environment': current_env,
            'datakit_version': datakit_version,
            'tables_ingested': TABLES_TO_INGEST,
            'execution_date': context['execution_date'].isoformat(),
            'warehouse': env_info['warehouse'],
        }

        # Store for monitoring/lineage
        # In prod, this might go to your metadata store
        if current_env == 'prod':
            # Write to production metadata store
            print(f"Recording to production metadata store: {json.dumps(metadata)}")
        else:
            # For non-prod, just use Airflow Variables
            Variable.set(
                f"last_bronze_ingestion_{current_env}",
                json.dumps(metadata),
                serialize_json=False
            )

        print(f"Ingestion completed in {current_env} environment")

    # Record metadata after all ingestions
    record_metadata = record_ingestion_metadata()
    ingestion_tasks >> record_metadata

# ==============================================================================
# DEPLOYMENT NOTES
# ==============================================================================
"""
LOCAL DEVELOPMENT (Docker Desktop):
====================================
1. Start local stack:
   cd datakits-sqlserver
   make dev-mock  # Start mock SQL Server
   make deploy    # Start Airflow with Docker

2. Access Airflow UI:
   http://localhost:8080 (admin/admin)

3. Set Variables:
   - mssql_server: mock-sqlserver
   - mssql_database: TestWarehouse

4. Trigger DAG manually


INTEGRATION/QA/PROD (Kubernetes):
==================================
1. Deploy via GitOps:
   git tag v1.2.3
   git push --tags
   # ArgoCD/Flux detects and deploys

2. Datakit images are pulled from:
   - INT: registry.int.company.com/datakits/
   - QA: registry.qa.company.com/datakits/
   - PROD: registry.prod.company.com/datakits/

3. Kerberos tickets from:
   - Secret: kerberos-tickets
   - Managed by: Delinea integration

4. Variables set via:
   - INT/QA: Terraform
   - PROD: Vault operator


VERSIONING STRATEGY:
====================
Datakits follow semantic versioning:
- v1.2.3 = Specific version
- v1.2.x = Patch updates auto-deploy to INT/QA
- v1.x.x = Minor updates need approval for PROD
- stable = Current production version
- latest = Development version (local only)


MONITORING:
===========
- Local: Logs in docker-compose logs
- K8s: Logs in Datadog/Splunk with tags:
  - datakit_name
  - datakit_version
  - environment
  - table_name
"""