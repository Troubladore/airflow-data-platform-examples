"""
SQL Server Connector with Kerberos/NT Authentication Support
"""
import os
import logging
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
import pyodbc
import pandas as pd
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SQLServerConfig(BaseModel):
    """Configuration for SQL Server connection with Kerberos."""

    server: str = Field(..., description="SQL Server hostname or IP")
    port: int = Field(default=1433, description="SQL Server port")
    database: str = Field(default="master", description="Database name")
    auth_type: str = Field(default="kerberos", description="Authentication type: kerberos, sql, azure_ad")

    # SQL Authentication fields (optional)
    username: Optional[str] = Field(default=None, description="Username for SQL auth")
    password: Optional[str] = Field(default=None, description="Password for SQL auth")

    # Connection options
    driver: str = Field(default="ODBC Driver 18 for SQL Server", description="ODBC driver")
    trust_server_certificate: bool = Field(default=False, description="Trust server certificate")
    encrypt: bool = Field(default=True, description="Use encryption")
    application_name: str = Field(default="DataKit-Bronze", description="Application name")
    connect_timeout: int = Field(default=30, description="Connection timeout in seconds")

    # Kerberos specific
    krb5_ccname: Optional[str] = Field(default=None, description="Kerberos ticket cache location")

    class Config:
        extra = "forbid"


class SQLServerKerberosConnector:
    """
    Connector for SQL Server with Kerberos/NT Authentication support.

    This connector handles:
    - Kerberos ticket-based authentication
    - SQL Server authentication fallback
    - Connection pooling and management
    - Bulk data operations
    """

    def __init__(self, config: SQLServerConfig):
        self.config = config
        self.engine: Optional[Engine] = None
        self._setup_kerberos_environment()

    def _setup_kerberos_environment(self):
        """Configure Kerberos environment variables if needed."""
        if self.config.auth_type == "kerberos":
            # Set KRB5CCNAME if provided
            if self.config.krb5_ccname:
                os.environ["KRB5CCNAME"] = self.config.krb5_ccname
            elif "KRB5CCNAME" not in os.environ:
                # Default to common location
                os.environ["KRB5CCNAME"] = "/krb5/cache/krb5cc"

            logger.info(f"Kerberos ticket cache: {os.environ.get('KRB5CCNAME')}")

    def _build_connection_string(self) -> str:
        """Build ODBC connection string based on authentication type."""
        params = [
            f"DRIVER={{{self.config.driver}}}",
            f"SERVER={self.config.server},{self.config.port}",
            f"DATABASE={self.config.database}",
        ]

        # Authentication parameters
        if self.config.auth_type == "kerberos":
            params.extend([
                "Trusted_Connection=Yes",
                "Authentication=Kerberos",
            ])
        elif self.config.auth_type == "azure_ad":
            params.extend([
                "Authentication=ActiveDirectoryIntegrated",
            ])
        else:  # SQL Authentication
            if not self.config.username:
                raise ValueError("SQL authentication requires username")
            params.extend([
                f"UID={self.config.username}",
                f"PWD={self.config.password or ''}",
            ])

        # Additional connection options
        if self.config.trust_server_certificate:
            params.append("TrustServerCertificate=Yes")

        if self.config.encrypt:
            params.append("Encrypt=Yes")

        params.append(f"APP={self.config.application_name}")
        params.append(f"Connection Timeout={self.config.connect_timeout}")

        conn_string = ";".join(params)

        # Log connection details (without sensitive info)
        logger.debug(f"Connection: {self.config.server}:{self.config.port}/{self.config.database} "
                    f"using {self.config.auth_type} authentication")

        return conn_string

    def get_connection(self) -> pyodbc.Connection:
        """Get a raw ODBC connection."""
        conn_string = self._build_connection_string()
        try:
            return pyodbc.connect(conn_string)
        except Exception as e:
            logger.error(f"Failed to connect to SQL Server: {e}")
            raise

    def get_engine(self) -> Engine:
        """Get SQLAlchemy engine."""
        if not self.engine:
            conn_string = self._build_connection_string()
            import urllib.parse
            encoded = urllib.parse.quote_plus(conn_string)
            url = f"mssql+pyodbc:///?odbc_connect={encoded}"

            self.engine = create_engine(
                url,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,  # Verify connections before using
                echo=False,
            )
        return self.engine

    @contextmanager
    def get_session(self):
        """Get SQLAlchemy session context manager."""
        engine = self.get_engine()
        with Session(engine) as session:
            yield session

    def test_connection(self) -> tuple[bool, str]:
        """Test the SQL Server connection."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT
                        @@VERSION as version,
                        SUSER_NAME() as login_name,
                        DB_NAME() as database_name
                """)
                result = cursor.fetchone()

                message = (
                    f"Connected successfully!\n"
                    f"  Login: {result.login_name}\n"
                    f"  Database: {result.database_name}\n"
                    f"  Version: {result.version[:100]}..."
                )

                logger.info(message)
                return True, message

        except Exception as e:
            error_msg = f"Connection failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def list_tables(self, schema: str = "dbo") -> List[str]:
        """List all tables in the specified schema."""
        engine = self.get_engine()
        inspector = inspect(engine)
        return inspector.get_table_names(schema=schema)

    def get_table_metadata(self, table_name: str, schema: str = "dbo") -> Dict[str, Any]:
        """Get metadata for a specific table."""
        engine = self.get_engine()
        inspector = inspect(engine)

        columns = inspector.get_columns(table_name, schema=schema)
        primary_keys = inspector.get_pk_constraint(table_name, schema=schema)
        foreign_keys = inspector.get_foreign_keys(table_name, schema=schema)

        # Get row count
        with engine.connect() as conn:
            result = conn.execute(
                text(f"SELECT COUNT(*) FROM [{schema}].[{table_name}]")
            ).scalar()
            row_count = result

        return {
            "schema": schema,
            "table": table_name,
            "columns": columns,
            "primary_keys": primary_keys,
            "foreign_keys": foreign_keys,
            "row_count": row_count,
        }

    def read_table(
        self,
        table_name: str,
        schema: str = "dbo",
        batch_size: int = 10000,
        columns: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Read data from a SQL Server table.

        Args:
            table_name: Name of the table to read
            schema: Schema name (default: dbo)
            batch_size: Number of rows to read at once
            columns: Specific columns to read (None for all)

        Returns:
            DataFrame with the table data
        """
        engine = self.get_engine()

        # Build query
        if columns:
            column_list = ", ".join([f"[{col}]" for col in columns])
            query = f"SELECT {column_list} FROM [{schema}].[{table_name}]"
        else:
            query = f"SELECT * FROM [{schema}].[{table_name}]"

        # Read data in chunks for memory efficiency
        chunks = []
        for chunk in pd.read_sql_query(
            query,
            engine,
            chunksize=batch_size
        ):
            chunks.append(chunk)
            logger.info(f"Read {len(chunk)} rows from {schema}.{table_name}")

        if chunks:
            df = pd.concat(chunks, ignore_index=True)
            logger.info(f"Total rows read: {len(df)}")
            return df
        else:
            return pd.DataFrame()

    def write_to_bronze(
        self,
        df: pd.DataFrame,
        target_table: str,
        target_schema: str = "bronze",
        if_exists: str = "append",
    ) -> int:
        """
        Write DataFrame to Bronze layer table.

        Args:
            df: DataFrame to write
            target_table: Target table name
            target_schema: Target schema (default: bronze)
            if_exists: How to behave if table exists (append, replace, fail)

        Returns:
            Number of rows written
        """
        engine = self.get_engine()

        # Ensure schema exists
        with engine.connect() as conn:
            conn.execute(text(f"""
                IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = '{target_schema}')
                BEGIN
                    EXEC('CREATE SCHEMA [{target_schema}]')
                END
            """))
            conn.commit()

        # Write data
        df.to_sql(
            name=target_table,
            con=engine,
            schema=target_schema,
            if_exists=if_exists,
            index=False,
            method="multi",  # Faster bulk insert
            chunksize=1000,
        )

        logger.info(f"Wrote {len(df)} rows to {target_schema}.{target_table}")
        return len(df)

    def execute_query(self, query: str, params: Optional[Dict] = None) -> List[tuple]:
        """Execute a SQL query and return results."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            if cursor.description:
                return cursor.fetchall()
            else:
                conn.commit()
                return []