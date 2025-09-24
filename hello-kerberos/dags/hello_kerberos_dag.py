"""
Hello Kerberos DAG - Demonstrates SQL Server connection with Windows Authentication
"""
import os
import subprocess
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator


def check_kerberos_tickets():
    """Check if Kerberos tickets are available in the container."""
    print("🔍 Checking for Kerberos tickets...")

    # Check common ticket locations
    ticket_locations = [
        "/tmp/krb5_cache/krb5cc_1000",
        "/tmp/krb5cc_1000",
        os.environ.get("KRB5CCNAME", "")
    ]

    ticket_found = False
    for location in ticket_locations:
        if location and os.path.exists(location):
            print(f"✅ Found ticket cache at: {location}")
            ticket_found = True

            # Try to list tickets
            try:
                result = subprocess.run(
                    ["klist"],
                    capture_output=True,
                    text=True,
                    env={**os.environ, "KRB5CCNAME": location}
                )
                if result.returncode == 0:
                    print("📋 Ticket details:")
                    print(result.stdout)
                else:
                    print("⚠️  Could not read ticket details")
            except FileNotFoundError:
                print("ℹ️  klist not available in container")
            break

    if not ticket_found:
        print("❌ No Kerberos tickets found!")
        print("   Run 'kinit YOUR_USERNAME@COMPANY.COM' in WSL2")
        print("   Then restart the platform services")
        raise Exception("Kerberos tickets not found")

    return "tickets_verified"


def test_sqlserver_connection():
    """Test SQL Server connection with Windows Authentication."""
    print("🔌 Testing SQL Server connection...")

    # Get configuration from environment
    server = os.environ.get("SQLSERVER_HOST", "your-server.company.com")
    database = os.environ.get("SQLSERVER_DATABASE", "master")

    try:
        import pyodbc

        # Connection string for Windows Authentication via Kerberos
        conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"Trusted_Connection=yes;"
            f"Authentication=ActiveDirectoryIntegrated;"
        )

        print(f"📊 Connecting to {server}/{database}...")

        # Attempt connection
        with pyodbc.connect(conn_str, timeout=10) as conn:
            cursor = conn.cursor()

            # Run a simple query
            cursor.execute("SELECT @@SERVERNAME as server, SYSTEM_USER as user, DB_NAME() as db")
            row = cursor.fetchone()

            print("✅ Successfully connected to SQL Server!")
            print(f"   Server: {row.server}")
            print(f"   Database: {row.db}")
            print(f"   User: {row.user}")

            return "connection_successful"

    except ImportError:
        print("❌ pyodbc not installed")
        print("   Add to requirements.txt: pyodbc==5.0.1")
        raise

    except pyodbc.Error as e:
        print(f"❌ Connection failed: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Verify SQL Server allows Kerberos authentication")
        print("2. Check server name and database are correct")
        print("3. Ensure Kerberos tickets are valid (kinit in WSL2)")
        print("4. Verify network connectivity to SQL Server")
        raise

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        raise


def show_auth_info():
    """Display authentication information."""
    print("🔐 Authentication Information")
    print("=" * 40)

    # Environment variables
    important_vars = [
        "KRB5CCNAME",
        "KRB5_CONFIG",
        "SQLSERVER_HOST",
        "SQLSERVER_DATABASE",
        "USER",
        "HOSTNAME"
    ]

    for var in important_vars:
        value = os.environ.get(var, "not set")
        print(f"{var}: {value}")

    # Check for ticket files
    print("\n📁 Ticket Locations:")
    for path in ["/tmp/krb5_cache", "/tmp", "/var/kerberos"]:
        if os.path.exists(path):
            files = os.listdir(path)
            krb_files = [f for f in files if f.startswith("krb")]
            if krb_files:
                print(f"  {path}: {krb_files}")

    return "auth_info_displayed"


# Define default arguments
default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 0,  # Don't retry auth failures
}

# Define the DAG
with DAG(
    'hello_kerberos_sqlserver',
    default_args=default_args,
    description='Test SQL Server connection with Kerberos authentication',
    schedule_interval=None,  # Manual trigger only
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['example', 'kerberos', 'sql-server'],
) as dag:

    # Task 1: Show authentication info
    show_auth = PythonOperator(
        task_id='show_auth_info',
        python_callable=show_auth_info,
    )

    # Task 2: Check Kerberos tickets
    check_tickets = PythonOperator(
        task_id='check_kerberos_tickets',
        python_callable=check_kerberos_tickets,
    )

    # Task 3: Test SQL Server connection
    test_connection = PythonOperator(
        task_id='test_sqlserver_connection',
        python_callable=test_sqlserver_connection,
    )

    # Task 4: Success message
    success_message = BashOperator(
        task_id='success_message',
        bash_command="""
        echo "🎉 Kerberos authentication working!"
        echo ""
        echo "You can now:"
        echo "1. Query SQL Server without passwords"
        echo "2. Use your Windows credentials automatically"
        echo "3. Deploy secure data pipelines"
        echo ""
        echo "Next: Check out datakits-sqlserver example for production patterns"
        """
    )

    # Define task dependencies
    show_auth >> check_tickets >> test_connection >> success_message