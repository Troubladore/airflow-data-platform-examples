"""
Bronze Pagila Ingestion DAG

Orchestrates the extraction and loading of Pagila database tables into the Bronze layer.
Uses Kerberos authentication for source database access.
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup
from airflow.models import Variable
from airflow.exceptions import AirflowException
from datetime import datetime, timedelta
import sys
import subprocess
import logging

# Add bronze_datakits_pagila to path
sys.path.insert(0, '/home/emaynard/repos/airflow-data-platform-examples/bronze-datakits-pagila')

logger = logging.getLogger(__name__)


def check_kerberos_ticket(**context):
    """Check if valid Kerberos ticket exists

    Args:
        **context: Airflow context

    Returns:
        True if valid ticket exists

    Raises:
        AirflowException: If no valid Kerberos ticket exists
    """
    logger.info("Checking for valid Kerberos ticket...")
    result = subprocess.run(['klist'], capture_output=True, text=True)

    if result.returncode != 0:
        logger.error("No valid Kerberos ticket found")
        raise AirflowException("No valid Kerberos ticket found. Please ensure ticket is mounted.")

    # Check for principal
    if 'Default principal:' not in result.stdout:
        logger.error("No Kerberos principal found in ticket")
        raise AirflowException("Invalid Kerberos ticket")

    logger.info(f"Found Kerberos ticket: {result.stdout[:200]}...")
    return True


def load_bronze_table(table_name: str, **context):
    """Load a single table from Pagila to Bronze layer

    Args:
        table_name: Name of the table to load
        **context: Airflow context

    Returns:
        Dictionary with load results
    """
    from bronze_datakits_pagila.loader import PagilaBronzeLoader

    # Get configuration from Airflow Variables
    source_host = Variable.get("bronze_source_host", default_var="sqlpg.eruditis.lab")
    source_database = Variable.get("bronze_source_db", default_var="pagila")
    target_db_url = Variable.get("bronze_target_db_url", default_var=None)

    logger.info(f"Loading table: {table_name}")
    logger.info(f"Source: {source_host}/{source_database}")
    logger.info(f"Target: {target_db_url[:50]}..." if target_db_url else "Target: None")

    try:
        # Initialize loader with Kerberos authentication
        loader = PagilaBronzeLoader(
            source_host=source_host,
            source_database=source_database,
            use_kerberos=True,
            target_db_url=target_db_url
        )

        # Load the table
        result = loader.load_table(table_name)

        # Push result to XCom for monitoring
        context['task_instance'].xcom_push(key='rows_loaded', value=result['rows_loaded'])
        context['task_instance'].xcom_push(key='table_name', value=table_name)

        logger.info(f"Successfully loaded {result['rows_loaded']} rows from {table_name}")
        return result

    except Exception as e:
        logger.error(f"Failed to load table {table_name}: {str(e)}")
        raise AirflowException(f"Failed to load table {table_name}: {str(e)}")


# Default arguments for all tasks
default_args = {
    'owner': 'data-platform',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'email_on_failure': False,
    'email_on_retry': False,
}

# Create the DAG
dag = DAG(
    'bronze_pagila_ingestion',
    default_args=default_args,
    description='Bronze layer ingestion from Pagila',
    schedule=None,  # Manual trigger initially
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['bronze', 'pagila'],
    max_active_runs=1,
)

# Table groups by size (from Issue #15 testing)
small_tables = ['language', 'category', 'country']  # < 500 rows
medium_tables = ['actor', 'address', 'city', 'customer', 'staff', 'store']  # 500-1500 rows
large_tables = ['film', 'inventory', 'film_actor', 'film_category']  # 1000-5000 rows
huge_tables = ['rental', 'payment']  # 10000+ rows

# Kerberos check task
kerberos_check = PythonOperator(
    task_id='check_kerberos',
    python_callable=check_kerberos_ticket,
    dag=dag,
)

# Create task groups for parallel execution
with TaskGroup("small_tables", tooltip="Tables with < 500 rows", dag=dag) as small_group:
    for table in small_tables:
        task = PythonOperator(
            task_id=f'load_{table}',
            python_callable=load_bronze_table,
            op_kwargs={'table_name': table},
            pool='bronze_loader_pool',  # Limit concurrency
        )

with TaskGroup("medium_tables", tooltip="Tables with 500-1500 rows", dag=dag) as medium_group:
    for table in medium_tables:
        task = PythonOperator(
            task_id=f'load_{table}',
            python_callable=load_bronze_table,
            op_kwargs={'table_name': table},
            pool='bronze_loader_pool',
        )

with TaskGroup("large_tables", tooltip="Tables with 1000-5000 rows", dag=dag) as large_group:
    for table in large_tables:
        task = PythonOperator(
            task_id=f'load_{table}',
            python_callable=load_bronze_table,
            op_kwargs={'table_name': table},
            pool='bronze_loader_pool',
        )

with TaskGroup("huge_tables", tooltip="Tables with 10000+ rows", dag=dag) as huge_group:
    for table in huge_tables:
        task = PythonOperator(
            task_id=f'load_{table}',
            python_callable=load_bronze_table,
            op_kwargs={'table_name': table},
            pool='bronze_loader_pool',
        )

# Define execution order
# Kerberos check runs first, then process tables from smallest to largest
kerberos_check >> small_group >> medium_group >> large_group >> huge_group