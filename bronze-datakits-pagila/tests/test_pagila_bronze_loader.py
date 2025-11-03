"""
Test Bronze Data Loader for Pagila Database

Tests the extraction and loading of Pagila data into Bronze tables
using the sqlmodel-framework's BronzeIngestionPipeline.
"""

import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch
import pytest
import pandas as pd
from datetime import datetime
from typing import List

# Add framework to path
sys.path.insert(0, '/home/emaynard/repos/airflow-data-platform/sqlmodel-framework/src')
sys.path.insert(0, '/home/emaynard/repos/airflow-data-platform-examples/bronze-datakits-pagila')

from sqlmodel_framework.base.loaders import BronzeIngestionPipeline
from bronze_datakits_pagila.models import LanguageBronze
from sqlalchemy import create_engine, text
from sqlalchemy_utils import database_exists, create_database, drop_database
from sqlmodel import SQLModel, Session, select


class TestPagilaBronzeLoader:
    """Test Bronze loader for Pagila database"""

    def test_extracts_language_table_from_source(self):
        """Test that loader can extract language table from Pagila source"""
        # Arrange - Create loader with source connection
        from bronze_datakits_pagila.loader import PagilaBronzeLoader

        loader = PagilaBronzeLoader(
            source_host="sqlpg.eruditis.lab",
            source_database="pagila",
            use_kerberos=True
        )

        # Act - Extract language table (smallest with 6 rows)
        df = loader.extract_table("language")

        # Assert - Verify extraction worked
        assert df is not None
        assert len(df) == 6  # Language table has exactly 6 rows
        assert "language_id" in df.columns
        assert "name" in df.columns
        assert "last_update" in df.columns

    def test_loads_language_to_bronze_database(self):
        """Test that loader can write language data to Bronze database"""
        # Arrange - Setup test Bronze database
        test_db_url = "postgresql://postgres:postgres@localhost:5433/test_bronze_pagila"

        # Ensure clean test database
        if database_exists(test_db_url):
            drop_database(test_db_url)
        create_database(test_db_url)

        # Create Bronze tables
        engine = create_engine(test_db_url)

        # Create schema first
        with engine.connect() as conn:
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS bronze"))
            conn.commit()

        # Create tables
        SQLModel.metadata.create_all(engine)

        # Create loader
        from bronze_datakits_pagila.loader import PagilaBronzeLoader

        loader = PagilaBronzeLoader(
            source_host="sqlpg.eruditis.lab",
            source_database="pagila",
            use_kerberos=True,
            target_db_url=test_db_url  # Add target database
        )

        # Act - Load language table to Bronze
        result = loader.load_table("language")

        # Assert - Verify data was loaded to Bronze database
        with Session(engine) as session:
            languages = session.exec(select(LanguageBronze)).all()
            assert len(languages) == 6

            # Check Bronze metadata was added
            for lang in languages:
                assert lang.bronze_load_timestamp is not None
                assert lang.bronze_source_system == "pagila_kerberos"
                assert lang.bronze_source_table == "language"
                assert lang.bronze_source_host == "sqlpg.eruditis.lab"
                assert lang.bronze_extraction_method == "full_snapshot"

        # Cleanup - dispose all connections before dropping
        engine.dispose()
        drop_database(test_db_url)

    def test_excludes_sensitive_fields_from_extraction(self):
        """Test that loader excludes sensitive/blob fields during extraction"""
        # Arrange - Create loader
        from bronze_datakits_pagila.loader import PagilaBronzeLoader

        loader = PagilaBronzeLoader(
            source_host="sqlpg.eruditis.lab",
            source_database="pagila",
            use_kerberos=True
        )

        # Act - Extract film table (has fulltext exclusion)
        df_film = loader.extract_table("film")

        # Assert - Verify fulltext field is NOT in extracted data
        assert "fulltext" not in df_film.columns, "fulltext should be excluded from film table"

        # Act - Extract staff table (has picture and password exclusions)
        df_staff = loader.extract_table("staff")

        # Assert - Verify picture and password fields are NOT in extracted data
        assert "picture" not in df_staff.columns, "picture should be excluded from staff table"
        assert "password" not in df_staff.columns, "password should be excluded from staff table"

        # Verify other required fields are present
        assert "staff_id" in df_staff.columns
        assert "first_name" in df_staff.columns
        assert "last_name" in df_staff.columns

    @pytest.mark.parametrize("table_name,expected_pk,expected_count_range", [
        ("actor", "actor_id", (100, 300)),
        ("address", "address_id", (500, 700)),
        ("category", "category_id", (10, 20)),
        ("city", "city_id", (500, 700)),
        ("country", "country_id", (100, 120)),
        ("customer", "customer_id", (500, 700)),
        ("film", "film_id", (900, 1100)),
        ("film_actor", None, (5000, 6000)),  # Composite PK
        ("film_category", None, (2000, 2500)),  # Composite PK - updated based on actual data
        ("inventory", "inventory_id", (4000, 5000)),
        ("language", "language_id", (5, 10)),
        ("payment", "payment_id", (14000, 17000)),  # Partitioned table
        ("rental", "rental_id", (15000, 17000)),
        ("staff", "staff_id", (1400, 1600)),  # Updated based on actual data
        ("store", "store_id", (400, 600)),  # Updated based on actual data
    ])
    def test_extracts_all_15_pagila_tables(self, table_name: str, expected_pk: str, expected_count_range: tuple):
        """Test that loader can extract all 15 Pagila tables with expected data"""
        # Arrange - Create loader
        from bronze_datakits_pagila.loader import PagilaBronzeLoader

        loader = PagilaBronzeLoader(
            source_host="sqlpg.eruditis.lab",
            source_database="pagila",
            use_kerberos=True
        )

        # Act - Extract the table
        df = loader.extract_table(table_name)

        # Assert - Verify extraction worked
        assert df is not None, f"Failed to extract {table_name}"
        assert len(df) > 0, f"No data extracted from {table_name}"

        # Check row count is in expected range
        min_count, max_count = expected_count_range
        assert min_count <= len(df) <= max_count, \
            f"{table_name} has {len(df)} rows, expected between {min_count} and {max_count}"

        # Check primary key exists (if not composite)
        if expected_pk:
            assert expected_pk in df.columns, f"Primary key {expected_pk} not found in {table_name}"

        # Check for last_update column (most Pagila tables have this)
        # Payment table doesn't have last_update
        if table_name != "payment":
            assert "last_update" in df.columns, f"last_update column missing from {table_name}"

        # Verify field exclusions are applied
        if table_name == "film":
            assert "fulltext" not in df.columns, "fulltext should be excluded from film"
        elif table_name == "staff":
            assert "picture" not in df.columns, "picture should be excluded from staff"
            assert "password" not in df.columns, "password should be excluded from staff"