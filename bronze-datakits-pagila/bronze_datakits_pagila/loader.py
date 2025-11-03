"""
Bronze Data Loader for Pagila Database

Implements data extraction from Pagila database using Kerberos authentication
and loads into Bronze tables using the sqlmodel-framework.
"""

import sys
import subprocess
import logging
from pathlib import Path
from typing import Optional, Dict
import pandas as pd
import psycopg2
from datetime import datetime

# Add framework to path
sys.path.insert(0, '/home/emaynard/repos/airflow-data-platform/sqlmodel-framework/src')

from sqlmodel_framework.base.loaders import BronzeIngestionPipeline
from sqlalchemy import create_engine, text
from sqlmodel import Session

# Import all Bronze models
from bronze_datakits_pagila.models import (
    ActorBronze,
    AddressBronze,
    CategoryBronze,
    CityBronze,
    CountryBronze,
    CustomerBronze,
    FilmBronze,
    FilmActorBronze,
    FilmCategoryBronze,
    InventoryBronze,
    LanguageBronze,
    PaymentBronze,
    RentalBronze,
    StaffBronze,
    StoreBronze,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PagilaBronzeLoader(BronzeIngestionPipeline):
    """Bronze loader for Pagila database with Kerberos authentication"""

    # Table to model mapping
    TABLE_MODEL_MAP = {
        "actor": ActorBronze,
        "address": AddressBronze,
        "category": CategoryBronze,
        "city": CityBronze,
        "country": CountryBronze,
        "customer": CustomerBronze,
        "film": FilmBronze,
        "film_actor": FilmActorBronze,
        "film_category": FilmCategoryBronze,
        "inventory": InventoryBronze,
        "language": LanguageBronze,
        "payment": PaymentBronze,
        "rental": RentalBronze,
        "staff": StaffBronze,
        "store": StoreBronze,
    }

    # Fields to exclude per table (sensitive data, blobs, derived fields)
    FIELD_EXCLUSIONS = {
        "film": ["fulltext"],  # tsvector derived field
        "staff": ["picture", "password"],  # blob and sensitive fields
    }

    def __init__(
        self,
        source_host: str,
        source_database: str,
        use_kerberos: bool = True,
        bronze_path: Optional[Path] = None,
        target_db_url: Optional[str] = None
    ):
        """Initialize Pagila Bronze loader

        Args:
            source_host: Database host (e.g., 'sqlpg.eruditis.lab')
            source_database: Database name (e.g., 'pagila')
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

    def _get_kerberos_username(self) -> Optional[str]:
        """Extract username from Kerberos ticket"""
        try:
            result = subprocess.run(['klist'], capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'Default principal:' in line:
                        principal = line.split(':')[1].strip()
                        username = principal.split('@')[0]
                        logger.info(f"Using Kerberos principal: {principal}")
                        return username
        except Exception:
            pass
        return None

    def _get_connection(self):
        """Create connection to Pagila with Kerberos"""
        conn_params = {
            'host': self.source_host,
            'port': '5432',
            'database': self.source_database,
        }

        if self.use_kerberos:
            conn_params['gssencmode'] = 'require'
            username = self._get_kerberos_username()
            if username:
                conn_params['user'] = username

        return psycopg2.connect(**conn_params)

    def extract_table(self, table_name: str, **kwargs) -> pd.DataFrame:
        """Extract data from source table with field exclusions

        Args:
            table_name: Name of table to extract
            **kwargs: Additional extraction parameters

        Returns:
            DataFrame with extracted data (excluded fields removed)
        """
        # Build SQLAlchemy connection string for Kerberos
        username = self._get_kerberos_username() if self.use_kerberos else None

        # Use psycopg2 as the driver with SQLAlchemy
        conn_str = f"postgresql+psycopg2://"
        if username:
            conn_str += f"{username}@"
        conn_str += f"{self.source_host}/{self.source_database}"
        if self.use_kerberos:
            conn_str += "?gssencmode=require"

        # Create engine with proper connection pooling
        engine = create_engine(conn_str, pool_pre_ping=True)
        try:
            # Build query with field exclusions
            excluded_fields = self.FIELD_EXCLUSIONS.get(table_name, [])

            if excluded_fields:
                # First, get all columns from the table
                with engine.connect() as conn:
                    result = conn.execute(
                        text(f"""
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE table_name = :table_name
                        AND table_schema = 'public'
                        """),
                        {"table_name": table_name}
                    )
                    all_columns = [row[0] for row in result]

                # Remove excluded fields
                columns_to_select = [col for col in all_columns if col not in excluded_fields]

                # Build explicit column list
                query = f"SELECT {', '.join(columns_to_select)} FROM {table_name}"
                logger.info(f"Extracting from {table_name} with exclusions: {excluded_fields}")
            else:
                query = f"SELECT * FROM {table_name}"

            df = pd.read_sql(query, engine)
            logger.info(f"Extracted {len(df)} rows from {table_name}")
            return df
        finally:
            engine.dispose()

    def load_table(self, table_name: str) -> Dict[str, any]:
        """Load a table from source to Bronze database

        Args:
            table_name: Name of table to load

        Returns:
            Dictionary with load results
        """
        # Extract data from source
        df = self.extract_table(table_name)

        # Add Bronze metadata
        df = self.add_bronze_metadata(
            df,
            source_system="pagila_kerberos",
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
                        # Convert row to dict and remove Bronze metadata we added
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
            source_system="pagila_kerberos",
            table_name=table_name,
            formats=['parquet', 'json']
        )

        return {
            "rows_loaded": len(df),
            "table": table_name,
            "paths": paths
        }