"""
SQL Server Source Connector
Layer 2: Source System Connection
"""
import os
import pyodbc
from typing import Optional


def get_connection_string() -> str:
    """Build connection string from environment."""
    server = os.environ.get("MSSQL_SERVER", "localhost")
    database = os.environ.get("MSSQL_DATABASE", "master")
    auth_type = os.environ.get("MSSQL_AUTH_TYPE", "kerberos")

    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={server};"
        f"DATABASE={database};"
    )

    if auth_type == "kerberos":
        conn_str += "Trusted_Connection=Yes;Authentication=Kerberos;"

    return conn_str


def test_connection() -> bool:
    """Test SQL Server connectivity."""
    try:
        conn_str = get_connection_string()
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            return True
    except Exception as e:
        print(f"Connection test failed: {e}")
        return False


def list_tables(schema: str = "dbo") -> list:
    """List available tables in source system."""
    conn_str = get_connection_string()
    tables = []

    with pyodbc.connect(conn_str) as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = '{schema}'
                AND TABLE_TYPE = 'BASE TABLE'
        """)
        tables = [row[0] for row in cursor.fetchall()]

    return tables