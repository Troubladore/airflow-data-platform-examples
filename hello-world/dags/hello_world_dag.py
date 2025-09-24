"""
Hello World DAG - Demonstrates basic Astronomer + Platform patterns
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

# Try to import platform framework (optional)
try:
    from sqlmodel_framework import ReferenceTable, TransactionalTable
    HAS_PLATFORM = True
except ImportError:
    HAS_PLATFORM = False


def check_platform():
    """Check if platform framework is available."""
    if HAS_PLATFORM:
        print("✅ SQLModel framework is available!")
        print("   - ReferenceTable for lookup data")
        print("   - TransactionalTable for event data")
        print("   - Automatic audit columns and triggers")
    else:
        print("ℹ️  SQLModel framework not installed")
        print("   To add it: pip install sqlmodel-framework @ git+...")
    return "platform_checked"


def hello_world():
    """Simple hello world task."""
    print("👋 Hello from Astronomer + Data Platform!")
    print(f"Current time: {datetime.now()}")
    return "hello_complete"


# Define default arguments
default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG
with DAG(
    'hello_world_platform',
    default_args=default_args,
    description='Hello World example with platform patterns',
    schedule_interval=None,  # Manual trigger only
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['example', 'hello-world'],
) as dag:

    # Task 1: Say hello
    say_hello = PythonOperator(
        task_id='say_hello',
        python_callable=hello_world,
    )

    # Task 2: Check platform
    check_platform_task = PythonOperator(
        task_id='check_platform',
        python_callable=check_platform,
    )

    # Task 3: Show environment
    show_env = BashOperator(
        task_id='show_environment',
        bash_command="""
        echo "=== Airflow Environment ==="
        echo "Airflow Home: $AIRFLOW_HOME"
        echo "Python: $(python --version)"
        echo "Working Dir: $(pwd)"
        echo ""
        echo "=== Platform Services ==="
        # Check if registry cache is available
        if curl -s http://host.docker.internal:5000/v2/_catalog > /dev/null 2>&1; then
            echo "✅ Registry cache is accessible"
        else
            echo "ℹ️  Registry cache not detected (optional)"
        fi
        """
    )

    # Define task dependencies
    say_hello >> check_platform_task >> show_env