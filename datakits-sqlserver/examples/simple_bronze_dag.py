"""
SIMPLE AIRFLOW DAG - SQL Server Bronze Ingestion with Kerberos
==============================================================

This DAG shows how to ingest ONE table from SQL Server daily using NT Authentication.

SETUP INSTRUCTIONS:
1. Copy this file to your Airflow dags/ folder
2. Update the CONFIGURATION section below
3. Ensure Kerberos sidecar is running (see README)
4. Create Airflow connection: 'mssql_bronze'

WHAT THIS DAG DOES:
- Runs daily at 2 AM
- Connects to SQL Server using Kerberos
- Ingests the Customer table to Bronze
- Sends email on success/failure
"""

from datetime import datetime, timedelta
from pathlib import Path
import os

from airflow import DAG
from airflow.decorators import task
from airflow.operators.email import EmailOperator

# ==============================================================================
# CONFIGURATION - UPDATE THESE FOR YOUR ENVIRONMENT
# ==============================================================================

# Step 1: Your SQL Server Details
CONFIG = {
    # Connection info - CHANGE THESE!
    "server": "sql.company.com",           # <- Your SQL Server hostname
    "port": 1433,                          # <- Usually 1433
    "database": "AdventureWorks",          # <- Your database name

    # Table to ingest - CHANGE THESE!
    "source_schema": "dbo",                # <- Schema containing your table
    "source_table": "Customer",            # <- Your table name

    # Bronze layer target
    "bronze_schema": "bronze",             # <- Target schema in Bronze
    "bronze_table": "customer_daily",      # <- Name in Bronze layer

    # Authentication (keep as kerberos for NT Auth)
    "auth_type": "kerberos",

    # Performance
    "batch_size": 10000,                   # <- Rows to process at once
}

# Step 2: DAG Schedule
SCHEDULE = "@daily"  # <- Change to your preferred schedule
                     # Options: "@hourly", "@daily", "@weekly", "0 2 * * *" (cron)

# Step 3: Email Notifications (optional)
EMAIL_ON_FAILURE = ["data-team@company.com"]  # <- Your email for alerts
EMAIL_ON_SUCCESS = []  # <- Leave empty to skip success emails

# ==============================================================================
# DAG DEFINITION
# ==============================================================================

# Default arguments for all tasks
default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'email': EMAIL_ON_FAILURE,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# Create the DAG
with DAG(
    'simple_sqlserver_bronze_ingestion',
    default_args=default_args,
    description='Ingest Customer table from SQL Server to Bronze using Kerberos',
    schedule_interval=SCHEDULE,
    start_date=datetime(2025, 1, 1),
    catchup=False,  # Don't run for past dates
    tags=['bronze', 'sql-server', 'kerberos', 'example'],
) as dag:

    # Task 1: Verify Kerberos ticket is valid
    @task
    def check_kerberos_ticket():
        """Verify we have a valid Kerberos ticket."""
        import subprocess

        print("🔍 Checking Kerberos ticket...")

        # Check ticket cache location
        krb5ccname = os.environ.get('KRB5CCNAME', '/krb5/cache/krb5cc')
        print(f"Ticket cache location: {krb5ccname}")

        if not os.path.exists(krb5ccname):
            raise FileNotFoundError(
                f"Kerberos ticket cache not found at {krb5ccname}. "
                "Make sure kerberos-sidecar is running!"
            )

        # Verify ticket is valid
        result = subprocess.run(
            ['klist', '-s'],
            capture_output=True
        )

        if result.returncode != 0:
            raise RuntimeError(
                "No valid Kerberos ticket! "
                "Check kerberos-sidecar logs: "
                "docker logs kerberos-sidecar"
            )

        # Show ticket details
        result = subprocess.run(
            ['klist'],
            capture_output=True,
            text=True
        )
        print("Current Kerberos ticket:")
        print(result.stdout)

        return {"status": "valid", "cache": krb5ccname}

    # Task 2: Test SQL Server connection
    @task
    def test_sql_connection():
        """Test that we can connect to SQL Server."""
        # Import here to avoid import errors if not installed
        from datakit_sqlserver_bronze import (
            SQLServerConfig,
            SQLServerKerberosConnector
        )

        print(f"🔌 Testing connection to {CONFIG['server']}/{CONFIG['database']}...")

        # Create configuration
        config = SQLServerConfig(
            server=CONFIG['server'],
            port=CONFIG['port'],
            database=CONFIG['database'],
            auth_type=CONFIG['auth_type'],
            trust_server_certificate=True,  # For self-signed certs
            application_name="Airflow-BronzeDAG"
        )

        # Test connection
        connector = SQLServerKerberosConnector(config)
        success, message = connector.test_connection()

        if not success:
            raise ConnectionError(f"SQL Server connection failed: {message}")

        print(f"✅ Connection successful: {message}")

        # Get table info
        metadata = connector.get_table_metadata(
            CONFIG['source_table'],
            CONFIG['source_schema']
        )

        return {
            "status": "connected",
            "server": CONFIG['server'],
            "database": CONFIG['database'],
            "table_rows": metadata['row_count'],
            "table_columns": len(metadata['columns'])
        }

    # Task 3: Ingest table to Bronze
    @task
    def ingest_to_bronze(connection_info: dict):
        """Ingest the configured table to Bronze layer."""
        from datakit_sqlserver_bronze import (
            SQLServerConfig,
            BronzeIngestionPipeline
        )
        from datetime import datetime

        print(f"🚀 Starting Bronze ingestion...")
        print(f"   Source: {CONFIG['source_schema']}.{CONFIG['source_table']}")
        print(f"   Target: {CONFIG['bronze_schema']}.{CONFIG['bronze_table']}")
        print(f"   Expected rows: {connection_info['table_rows']:,}")

        # Create configuration
        config = SQLServerConfig(
            server=CONFIG['server'],
            port=CONFIG['port'],
            database=CONFIG['database'],
            auth_type=CONFIG['auth_type'],
            trust_server_certificate=True,
            application_name="Airflow-BronzeDAG"
        )

        # Create pipeline
        pipeline = BronzeIngestionPipeline(config)

        # Run ingestion
        start_time = datetime.now()

        rows_ingested = pipeline.ingest_table(
            source_table=CONFIG['source_table'],
            source_schema=CONFIG['source_schema'],
            target_table=CONFIG['bronze_table'],
            target_schema=CONFIG['bronze_schema'],
            batch_size=CONFIG['batch_size']
        )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        result = {
            "rows_ingested": rows_ingested,
            "duration_seconds": duration,
            "rows_per_second": rows_ingested / duration if duration > 0 else 0,
            "source_table": f"{CONFIG['source_schema']}.{CONFIG['source_table']}",
            "target_table": f"{CONFIG['bronze_schema']}.{CONFIG['bronze_table']}",
            "ingestion_time": datetime.now().isoformat()
        }

        print(f"✅ Ingestion complete!")
        print(f"   Rows: {rows_ingested:,}")
        print(f"   Duration: {duration:.2f} seconds")
        print(f"   Rate: {result['rows_per_second']:.0f} rows/second")

        return result

    # Task 4: Log results
    @task
    def log_results(ingestion_result: dict):
        """Log the ingestion results for monitoring."""
        from airflow.models import Variable
        import json

        print("📊 Ingestion Summary:")
        print(json.dumps(ingestion_result, indent=2))

        # Optionally store in Airflow Variable for monitoring
        try:
            Variable.set(
                "last_bronze_ingestion",
                json.dumps(ingestion_result),
                serialize_json=False
            )
        except:
            pass  # Variable storage is optional

        # You could also:
        # - Write to a database
        # - Send to monitoring system
        # - Update a dashboard

        return ingestion_result

    # Optional Task 5: Send success email
    @task.branch
    def check_if_send_email(result: dict):
        """Decide whether to send success email."""
        if EMAIL_ON_SUCCESS:
            return 'send_success_email'
        else:
            return 'skip_email'

    # Email task (conditional)
    send_success_email = EmailOperator(
        task_id='send_success_email',
        to=EMAIL_ON_SUCCESS,
        subject=f'Bronze Ingestion Success - {CONFIG["source_table"]}',
        html_content="""
        <h3>Bronze Ingestion Completed Successfully</h3>
        <p>Table: {{ params.source_table }}</p>
        <p>Rows Ingested: {{ params.rows_ingested }}</p>
        <p>Duration: {{ params.duration }} seconds</p>
        """,
        trigger_rule='none_failed_or_skipped'
    )

    # Empty task for skip branch
    @task
    def skip_email():
        """Skip email notification."""
        pass

    # ==============================================================================
    # TASK DEPENDENCIES
    # ==============================================================================

    # Define the workflow
    ticket_check = check_kerberos_ticket()
    connection_test = test_sql_connection()
    ingestion = ingest_to_bronze(connection_test)
    results = log_results(ingestion)
    branch = check_if_send_email(results)

    # Set up the flow
    ticket_check >> connection_test >> ingestion >> results >> branch
    branch >> [send_success_email, skip_email()]

# ==============================================================================
# USAGE INSTRUCTIONS
# ==============================================================================
"""
TO USE THIS DAG:

1. Update the CONFIG section with your SQL Server details
2. Copy to your Airflow dags folder
3. Ensure kerberos-sidecar is running:
   docker-compose up -d kerberos-sidecar

4. Check in Airflow UI:
   - DAG should appear as 'simple_sqlserver_bronze_ingestion'
   - Click to view
   - Trigger manually or wait for schedule

5. Monitor execution:
   - Check task logs for details
   - Email alerts on failure
   - Results stored in Airflow Variables

TROUBLESHOOTING:
- If "No Kerberos ticket": Check kerberos-sidecar logs
- If "Connection failed": Verify SQL Server is accessible
- If "Table not found": Check table name and permissions
"""