"""
Bronze Data Loader for AdventureWorksLT Database (SQL Server)

Implements data extraction from SQL Server using Kerberos authentication via sqlcmd
and loads into Bronze tables using the sqlmodel-framework.
"""

import sys
import subprocess
import logging
import io
from pathlib import Path
from typing import Optional, Dict
import pandas as pd
from datetime import datetime

# Add framework to path
sys.path.insert(0, '/home/emaynard/repos/airflow-data-platform/sqlmodel-framework/src')

from sqlmodel_framework.base.loaders import BronzeIngestionPipeline
from sqlalchemy import create_engine
from sqlmodel import Session

# Import all Bronze models
from bronze_datakits_adventureworkslt.models import ProductCategoryBronze

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AdventureWorksLTBronzeLoader(BronzeIngestionPipeline):
    """Bronze loader for AdventureWorksLT database with Kerberos authentication"""

    # Table to model mapping (schema.table format for SQL Server)
    TABLE_MODEL_MAP = {
        "SalesLT.ProductCategory": ProductCategoryBronze,
    }

    def __init__(
        self,
        source_host: str,
        source_database: str,
        use_kerberos: bool = True,
        bronze_path: Optional[Path] = None,
        target_db_url: Optional[str] = None
    ):
        """Initialize AdventureWorksLT Bronze loader

        Args:
            source_host: SQL Server host (e.g., 'sql1.eruditis.lab')
            source_database: Database name (e.g., 'AdventureWorksLT')
            use_kerberos: Whether to use Kerberos authentication
            bronze_path: Path to Bronze storage (defaults to /tmp/bronze)
            target_db_url: URL for target Bronze database
        """
        self.source_host = source_host
        self.source_database = source_database
        self.use_kerberos = use_kerberos
        self.target_db_url = target_db_url

        # Set Bronze path
        if bronze_path is None:
            bronze_path = Path("/tmp/bronze")

        # Initialize parent with None connector (we'll manage connections ourselves)
        super().__init__(connector=None, bronze_path=bronze_path)

    def extract_table(self, table_name: str, **kwargs) -> pd.DataFrame:
        """Extract data from source table using sqlcmd with Kerberos

        Args:
            table_name: Name of table to extract (e.g., 'SalesLT.ProductCategory')
            **kwargs: Additional extraction parameters

        Returns:
            DataFrame with extracted data
        """
        # Build sqlcmd command for Kerberos auth
        cmd = [
            "sqlcmd",
            "-S", self.source_host,
            "-d", self.source_database,
            "-G",  # Use Kerberos authentication
            "-C",  # Trust server certificate
            "-Q", f"SET NOCOUNT ON; SELECT * FROM {table_name}",
            "-s", ",",  # Use comma as delimiter
            "-W",  # Remove trailing spaces
            "-h", "-1"  # No headers in output (we'll add them)
        ]

        try:
            # First get column names
            col_cmd = [
                "sqlcmd",
                "-S", self.source_host,
                "-d", self.source_database,
                "-G",
                "-C",
                "-Q", f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = '{table_name.split('.')[0]}' AND TABLE_NAME = '{table_name.split('.')[1]}' ORDER BY ORDINAL_POSITION",
                "-h", "-1",
                "-W"
            ]

            col_result = subprocess.run(col_cmd, capture_output=True, text=True, check=True)
            columns = [line.strip() for line in col_result.stdout.strip().split('\n') if line.strip()]

            logger.info(f"Columns for {table_name}: {columns}")

            # Now get the data
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            if not result.stdout.strip():
                logger.warning(f"No data returned from {table_name}")
                return pd.DataFrame(columns=columns)

            # Parse CSV output
            df = pd.read_csv(
                io.StringIO(result.stdout),
                names=columns,
                skipinitialspace=True
            )

            # Convert column names to lowercase (SQL Server uses PascalCase)
            df.columns = [col.lower() for col in df.columns]

            logger.info(f"Extracted {len(df)} rows from {table_name}")
            return df

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to extract {table_name}: {e.stderr}")
            raise
        except Exception as e:
            logger.error(f"Error extracting {table_name}: {str(e)}")
            raise

    def load_table(self, table_name: str) -> Dict[str, any]:
        """Load a table from source to Bronze database

        Args:
            table_name: Name of table to load (e.g., 'SalesLT.ProductCategory')

        Returns:
            Dictionary with load results
        """
        # Extract data from source
        df = self.extract_table(table_name)

        if df.empty:
            logger.warning(f"No data to load for {table_name}")
            return {"rows_loaded": 0, "table": table_name, "paths": []}

        # Replace NaN with None for proper NULL handling in database
        # pandas reads NULL integers as NaN (float), which causes issues with PostgreSQL
        df = df.replace({pd.NA: None, pd.NaT: None})
        import numpy as np
        df = df.replace({np.nan: None})

        # Add Bronze metadata
        df = self.add_bronze_metadata(
            df,
            source_system="adventureworkslt_kerberos",
            source_table=table_name,
            source_host=self.source_host,
            extraction_method="full_snapshot"
        )

        # Get the corresponding model class
        model_class = self.TABLE_MODEL_MAP.get(table_name)
        if not model_class:
            raise ValueError(f"No model found for table: {table_name}")

        # Write to Bronze database if configured
        if self.target_db_url:
            engine = create_engine(self.target_db_url)
            try:
                with Session(engine) as session:
                    # Convert DataFrame to model instances
                    for _, row in df.iterrows():
                        # Convert row to dict
                        row_dict = row.to_dict()

                        # Create model instance
                        instance = model_class(**row_dict)
                        session.add(instance)

                    session.commit()
                    logger.info(f"Loaded {len(df)} rows to Bronze database for {table_name}")
            finally:
                engine.dispose()

        # Also write to file storage (parquet/json)
        paths = self.write_bronze(
            df,
            source_system="adventureworkslt_kerberos",
            table_name=table_name.replace('.', '_'),  # Use underscore for file names
            formats=['parquet', 'json']
        )

        return {
            "rows_loaded": len(df),
            "table": table_name,
            "paths": paths
        }
